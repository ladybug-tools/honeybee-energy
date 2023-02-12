"""Module for computing Performance Cost Index (PCI) from baseline simulation results."""
import os

from ladybug.sql import SQLiteResult
from ladybug.futil import csv_to_matrix


UNREGULATED_USES = ('Interior Equipment', 'Exterior Equipment', 'Generators')


def comparison_from_sql(
        proposed_sql, baseline_sqls, climate_zone, building_type='NonResidential',
        electricity_cost=0.12, natural_gas_cost=0.06, district_cooling_cost=0.04,
        district_heating_cost=0.08, electricity_emissions=400):
    """Get a dictionary comparing baseline and proposed simulations from EnergyPlus SQLs.

    Args:
        proposed_sql: The path of the SQL result file that has been generated from an
            energy simulation of a proposed building.
        baseline_sqls: The path of the SQL result file that has been generated from an
            energy simulation of a baseline building. This can also be a list of SQL
            result files (eg. for several simulations of different orientations)
            in which case the PCI will be computed as the average across all files.
            Lastly, it can be a directory or list of directories containing results,
            in which case, the target PCI will be calculated form all files
            ending in .sql.
        climate_zone: Text indicating the ASHRAE climate zone. This can be a single
            integer (in which case it is interpreted as A) or it can include the
            A, B, or C qualifier (eg. 3C).
        building_type: Text for the building type that the Model represents. This is
            used to determine the baseline window-to-wall ratio and HVAC system. If
            the type is not recognized or is "Unknown", it will be assumed that the
            building is a generic NonResidential. The following have specified
            meaning per the standard.

            * NonResidential
            * Residential
            * MidriseApartment
            * HighriseApartment
            * LargeOffice
            * MediumOffice
            * SmallOffice
            * Retail
            * StripMall
            * PrimarySchool
            * SecondarySchool
            * SmallHotel
            * LargeHotel
            * Hospital
            * Outpatient
            * Warehouse
            * SuperMarket
            * FullServiceRestaurant
            * QuickServiceRestaurant
            * Laboratory
            * Courthouse

        electricity_cost: A number for the cost per each kWh of electricity. This
            can be in any currency as long as it is coordinated with the costs of
            other inputs to this method. (Default: 0.12 for the average 2020
            cost of electricity in the US in $/kWh).
        natural_gas_cost: A number for the cost per each kWh of natural gas. This
            can be in any currency as long as it is coordinated with the
            other inputs to this method. (Default: 0.06 for the average 2020
            cost of natural gas in the US in $/kWh).
        district_cooling_cost: A number for the cost per each kWh of district cooling
            energy. This can be in any currency as long as it is coordinated with the
            other inputs to this method. (Default: 0.04 assuming average 2020 US
            cost of electricity in $/kWh with a COP 3.5 chiller).
        district_heating_cost: A number for the cost per each kWh of district heating
            energy. This can be in any currency as long as it is coordinated with the
            other inputs to this method. (Default: 0.08 assuming average 2020 US
            cost of natural gas in $/kWh with an efficiency of 0.75 with all burner
            and distribution losses).
        electricity_emissions: A number for the electric grid carbon emissions
            in kg CO2 per MWh. For locations in the USA, this can be obtained from
            he honeybee_energy.result.emissions future_electricity_emissions method.
            For locations outside of the USA where specific data is unavailable,
            the following rules of thumb may be used as a guide. (Default: 400).

            * 800 kg/MWh - for an inefficient coal or oil-dominated grid
            * 400 kg/MWh - for the US (energy mixed) grid around 2020
            * 100-200 kg/MWh - for grids with majority renewable/nuclear composition
            * 0-100 kg/MWh - for grids with renewables and storage

    Returns:
        A dictionary with several keys.

        -   proposed_eui -- A number for the proposed end use intensity. Specifically,
            this is the sum of all electricity, fuel, district heating/cooling,
            etc. divided by the gross floor area (including both conditioned
            and unconditioned spaces). Units are kWh/m2.

        -   proposed_energy -- A number for the total energy use of the proposed
            building in kWh.

        -   proposed_cost -- A number for the total annual energy cost of the
            proposed building.

        -   proposed_carbon -- A number for the total annual operational carbon
            emissions of the proposed building in kg of C02.

        -   baseline_eui -- A number for the baseline end use intensity. Specifically,
            this is the sum of all electricity, fuel, district heating/cooling,
            etc. divided by the gross floor area (including both conditioned
            and unconditioned spaces). Units are kWh/m2.

        -   baseline_energy -- A number for the total energy use of the baseline
            building in kWh.

        -   baseline_cost -- A number for the total annual energy cost of the
            baseline building.

        -   baseline_carbon -- A number for the total annual operational carbon
            emissions of the baseline building in kg of C02.

        -   pci_t_2016 -- A fractional number for the target PCI for ASHRAE 90.1-2016.

        -   pci_t_2019 -- A fractional number for the target PCI for ASHRAE 90.1-2019.

        -   pci_t_2022 -- A fractional number for the target PCI for ASHRAE 90.1-2022.

        -   pci -- A fractional number for the PCI of the proposed building.

        -   pci_improvement_2016 -- A number less than 100 for the percentage better
            that the proposed building is over the target PCI for ASHRAE 90.1-2016.
            Negative numbers indicate a proposed building that is worse than
            the 2016 target PCI.

        -   pci_improvement_2019 -- A number less than 100 for the percentage better
            that the proposed building is over the target PCI for ASHRAE 90.1-2019.
            Negative numbers indicate a proposed building that is worse than
            the 2019 target PCI.

        -   pci_improvement_2022 -- A number less than 100 for the percentage better
            that the proposed building is over the target PCI for ASHRAE 90.1-2022.
            Negative numbers indicate a proposed building that is worse than
            the 2022 target PCI.

        -   carbon_t_2016 -- A fractional number for the target carbon index
            for ASHRAE 90.1-2016.

        -   carbon_t_2019 -- A fractional number for the target carbon index
            for ASHRAE 90.1-2019.

        -   carbon_t_2022 -- A fractional number for the target carbon index
            for ASHRAE 90.1-2022.

        -   pci_carbon -- A fractional number for the performance improvement
            of the proposed building in terms of carbon emissions.

        -   carbon_improvement_2016 -- A number less than 100 for the percentage better
            that the proposed building is over the target carbon for ASHRAE 90.1-2016.
            Negative numbers indicate a proposed building that is worse than
            the 2016 target.

        -   carbon_improvement_2019 -- A number less than 100 for the percentage better
            that the proposed building is over the target carbon for ASHRAE 90.1-2019.
            Negative numbers indicate a proposed building that is worse than
            the 2019 target.

        -   carbon_improvement_2022 -- A number less than 100 for the percentage better
            that the proposed building is over the target carbon for ASHRAE 90.1-2022.
            Negative numbers indicate a proposed building that is worse than
            the 2022 target.
    """
    # compute the target PCI from the baseline simulations
    base_dict = pci_target_from_baseline_sql(
        baseline_sqls, climate_zone, building_type,
        electricity_cost, natural_gas_cost, district_cooling_cost, district_heating_cost,
        electricity_emissions)
    # compute the energy cost of the proposed building
    result_dict = energy_cost_from_proposed_sql(
        proposed_sql, electricity_cost, natural_gas_cost,
        district_cooling_cost, district_heating_cost, electricity_emissions)
    result_dict.update(base_dict)
    # compute the improvement indices for energy cost
    pci = result_dict['proposed_cost'] / result_dict['baseline_cost']
    t_2016 = result_dict['pci_t_2016']
    t_2019 = result_dict['pci_t_2019']
    t_2022 = result_dict['pci_t_2022']
    result_dict['pci'] = round(pci, 3)
    result_dict['pci_improvement_2016'] = round(((t_2016 - pci) / t_2016) * 100, 3)
    result_dict['pci_improvement_2019'] = round(((t_2019 - pci) / t_2019) * 100, 3)
    result_dict['pci_improvement_2022'] = round(((t_2022 - pci) / t_2022) * 100, 3)
    # compute the improvement indices for energy cost
    pci_c = result_dict['proposed_carbon'] / result_dict['baseline_carbon']
    tc_2016 = result_dict['carbon_t_2016']
    tc_2019 = result_dict['carbon_t_2019']
    tc_2022 = result_dict['carbon_t_2022']
    result_dict['pci_carbon'] = pci_c
    result_dict['carbon_improvement_2016'] = \
        round(((tc_2016 - pci_c) / tc_2016) * 100, 3)
    result_dict['carbon_improvement_2019'] = \
        round(((tc_2019 - pci_c) / tc_2019) * 100, 3)
    result_dict['carbon_improvement_2022'] = \
        round(((tc_2022 - pci_c) / tc_2022) * 100, 3)
    return result_dict


def pci_target_from_baseline_sql(
        sql_results, climate_zone, building_type='NonResidential',
        electricity_cost=0.12, natural_gas_cost=0.06,
        district_cooling_cost=0.04, district_heating_cost=0.08,
        electricity_emissions=400):
    """Get a dictionary of target Performance Cost Indices from EnergyPlus SQLs.

    Args:
        sql_results: The path of the SQL result file that has been generated from an
            energy simulation of a baseline building. This can also be a list of SQL
            result files (eg. for several simulations of different orientations)
            in which case the PCI will be computed as the average across all files.
            Lastly, it can be a directory or list of directories containing results,
            in which case, the target PCI will be calculated form all files
            ending in .sql.
        climate_zone: Text indicating the ASHRAE climate zone. This can be a single
            integer (in which case it is interpreted as A) or it can include the
            A, B, or C qualifier (eg. 3C).
        building_type: Text for the building type that the Model represents. This is
            used to determine the baseline window-to-wall ratio and HVAC system. If
            the type is not recognized or is "Unknown", it will be assumed that the
            building is a generic NonResidential. The following have specified
            meaning per the standard.

            * NonResidential
            * Residential
            * MidriseApartment
            * HighriseApartment
            * LargeOffice
            * MediumOffice
            * SmallOffice
            * Retail
            * StripMall
            * PrimarySchool
            * SecondarySchool
            * SmallHotel
            * LargeHotel
            * Hospital
            * Outpatient
            * Warehouse
            * SuperMarket
            * FullServiceRestaurant
            * QuickServiceRestaurant
            * Laboratory
            * Courthouse

        electricity_cost: A number for the cost per each kWh of electricity. This
            can be in any currency as long as it is coordinated with the costs of
            other inputs to this method. (Default: 0.12 for the average 2020
            cost of electricity in the US in $/kWh).
        natural_gas_cost: A number for the cost per each kWh of natural gas. This
            can be in any currency as long as it is coordinated with the
            other inputs to this method. (Default: 0.06 for the average 2020
            cost of natural gas in the US in $/kWh).
        district_cooling_cost: A number for the cost per each kWh of district cooling
            energy. This can be in any currency as long as it is coordinated with the
            other inputs to this method. (Default: 0.04 assuming average 2020 US
            cost of electricity in $/kWh with a COP 3.5 chiller).
        district_heating_cost: A number for the cost per each kWh of district heating
            energy. This can be in any currency as long as it is coordinated with the
            other inputs to this method. (Default: 0.08 assuming average 2020 US
            cost of natural gas in $/kWh with an efficiency of 0.75 with all burner
            and distribution losses).
        electricity_emissions: A number for the electric grid carbon emissions
            in kg CO2 per MWh. For locations in the USA, this can be obtained from
            he honeybee_energy.result.emissions future_electricity_emissions method.
            For locations outside of the USA where specific data is unavailable,
            the following rules of thumb may be used as a guide. (Default: 400).

            * 800 kg/MWh - for an inefficient coal or oil-dominated grid
            * 400 kg/MWh - for the US (energy mixed) grid around 2020
            * 100-200 kg/MWh - for grids with majority renewable/nuclear composition
            * 0-100 kg/MWh - for grids with renewables and storage

    Returns:
        A dictionary with several keys.

        -   baseline_eui -- A number for the total end use intensity. Specifically,
            this is the sum of all electricity, fuel, district heating/cooling,
            etc. divided by the gross floor area (including both conditioned
            and unconditioned spaces). Units are kWh/m2.

        -   baseline_energy -- A number for the total energy use of the baseline
            building in kWh.

        -   baseline_cost -- A number for the total annual energy cost of the
            baseline building.

        -   baseline_carbon -- A number for the total annual operational carbon
            emissions of the baseline building in kg of C02.

        -   pci_t_2016 -- A fractional number for the target PCI for ASHRAE 90.1-2016.

        -   pci_t_2019 -- A fractional number for the target PCI for ASHRAE 90.1-2019.

        -   pci_t_2022 -- A fractional number for the target PCI for ASHRAE 90.1-2022.

        -   carbon_t_2016 -- A fractional number for the target carbon index
            for ASHRAE 90.1-2016.

        -   carbon_t_2019 -- A fractional number for the target carbon index
            for ASHRAE 90.1-2019.

        -   carbon_t_2022 -- A fractional number for the target carbon index
            for ASHRAE 90.1-2022.
    """
    # create a list of sql file path that were either passed directly or are
    # contained within passed folders
    if not isinstance(sql_results, (list, tuple)):
        sql_results = [sql_results]
    sql_paths = []
    for file_or_folder_path in sql_results:
        if os.path.isdir(file_or_folder_path):
            for file_path in os.listdir(file_or_folder_path):
                if file_path.endswith('.sql'):
                    sql_paths.append(os.path.join(file_or_folder_path, file_path))
        else:
            sql_paths.append(file_or_folder_path)

    # parse the regulated and unregulated energy use from the sql
    # loop through the sql files and add the energy use
    total_floor_area = 0
    bbu_energy, bbr_energy = 0, 0
    bbu_cost, bbr_cost = 0, 0
    bbu_carbon, bbr_carbon = 0, 0
    for sql_path in sql_paths:
        # parse the SQL file
        sql_obj = SQLiteResult(sql_path)
        # get the total floor area of the model
        area_dict = sql_obj.tabular_data_by_name('Building Area')
        areas = tuple(area_dict.values())
        try:
            total_floor_area += areas[0][0]
        except IndexError:
            msg = 'Failed to find the "Building Area" table in the .sql file.'
            raise ValueError(msg)
        # get the energy use
        eui_dict = sql_obj.tabular_data_by_name('End Uses')
        for category, vals in eui_dict.items():
            try:
                vals = [float(v) for v in vals[:12]]
            except ValueError:
                break  # we hit the end of the table
            ele = (vals[0] * electricity_emissions) / 1000
            gas = (vals[1] * 277.358) / 1000
            dce = (vals[10] * (electricity_emissions / 3.5)) / 1000
            dhe = (vals[11] * 369.811) / 1000
            if category in UNREGULATED_USES:
                bbu_energy += sum(vals)
                bbu_cost += vals[0] * electricity_cost
                bbu_cost += vals[1] * natural_gas_cost
                bbu_cost += vals[10] * district_cooling_cost
                bbu_cost += vals[11] * district_heating_cost
                bbu_carbon += sum([ele, gas, dce, dhe])
            else:
                bbr_energy += sum(vals)
                bbr_cost += vals[0] * electricity_cost
                bbr_cost += vals[1] * natural_gas_cost
                bbr_cost += vals[10] * district_cooling_cost
                bbr_cost += vals[11] * district_heating_cost
                bbr_carbon += sum([ele, gas, dce, dhe])
    # divide the results by number of SQLs if there are several of them
    if len(sql_paths) != 1:
        total_floor_area = total_floor_area / len(sql_paths)
        bbu_energy = bbu_energy / len(sql_paths)
        bbr_energy = bbr_energy / len(sql_paths)
        bbu_cost = bbu_cost / len(sql_paths)
        bbr_cost = bbr_cost / len(sql_paths)
        bbu_carbon = bbu_carbon / len(sql_paths)
        bbr_carbon = bbr_carbon / len(sql_paths)

    # process the input climate zone
    if len(climate_zone) == 1 and climate_zone not in ('7', '8'):
        climate_zone = '{}A'.format(climate_zone)

    # load the building performance factors from the tables
    pci_2016_file = os.path.join(os.path.dirname(__file__), 'data', 'pci_2016.csv')
    pci_2016_data = csv_to_matrix(pci_2016_file)
    cz_i = pci_2016_data[0].index(climate_zone)
    bpf_2016 = float(pci_2016_data[1][cz_i])
    for row in pci_2016_data[1:]:
        if row[0] == building_type:
            bpf_2016 = float(row[cz_i])
            break
    pci_2019_file = os.path.join(os.path.dirname(__file__), 'data', 'pci_2019.csv')
    pci_2019_data = csv_to_matrix(pci_2019_file)
    cz_i = pci_2019_data[0].index(climate_zone)
    bpf_2019 = float(pci_2019_data[1][cz_i])
    for row in pci_2019_data[1:]:
        if row[0] == building_type:
            bpf_2019 = float(row[cz_i])
            break
    pci_2022_file = os.path.join(os.path.dirname(__file__), 'data', 'pci_2022.csv')
    pci_2022_data = csv_to_matrix(pci_2022_file)
    cz_i = pci_2022_data[0].index(climate_zone)
    bpf_2022 = float(pci_2022_data[1][cz_i])
    for row in pci_2022_data[1:]:
        if row[0] == building_type:
            bpf_2022 = float(row[cz_i])
            break

    # put all metrics into a final dictionary
    total_energy = bbu_energy + bbr_energy
    total_cost = bbu_cost + bbr_cost
    total_carbon = bbu_carbon + bbr_carbon
    result_dict = {
        'baseline_eui': round(total_energy / total_floor_area, 3),
        'baseline_energy': round(total_energy, 3),
        'baseline_cost': round(total_cost, 2),
        'baseline_carbon': round(total_carbon, 3),
        'pci_t_2016': round((bbu_cost + (bpf_2016 * bbr_cost)) / total_cost, 3),
        'pci_t_2019': round((bbu_cost + (bpf_2019 * bbr_cost)) / total_cost, 3),
        'pci_t_2022': round((bbu_cost + (bpf_2022 * bbr_cost)) / total_cost, 3),
        'carbon_t_2016': round((bbu_carbon + (bpf_2016 * bbr_carbon)) / total_carbon, 3),
        'carbon_t_2019': round((bbu_carbon + (bpf_2019 * bbr_carbon)) / total_carbon, 3),
        'carbon_t_2022': round((bbu_carbon + (bpf_2022 * bbr_carbon)) / total_carbon, 3)
    }
    return result_dict


def energy_cost_from_proposed_sql(
        sql_result, electricity_cost=0.12, natural_gas_cost=0.06,
        district_cooling_cost=0.04, district_heating_cost=0.08,
        electricity_emissions=400):
    """Get a dictionary of proposed energy cost from an EnergyPlus SQL.

    Args:
        sql_result: The path of the SQL result file that has been generated from an
            energy simulation of a proposed building.
        electricity_cost: A number for the cost per each kWh of electricity. This
            can be in any currency as long as it is coordinated with the costs of
            other inputs to this method. (Default: 0.12 for the average 2020
            cost of electricity in the US in $/kWh).
        natural_gas_cost: A number for the cost per each kWh of natural gas. This
            can be in any currency as long as it is coordinated with the
            other inputs to this method. (Default: 0.06 for the average 2020
            cost of natural gas in the US in $/kWh).
        district_cooling_cost: A number for the cost per each kWh of district cooling
            energy. This can be in any currency as long as it is coordinated with the
            other inputs to this method. (Default: 0.04 assuming average 2020 US
            cost of electricity in $/kWh with a COP 3.5 chiller).
        district_heating_cost: A number for the cost per each kWh of district heating
            energy. This can be in any currency as long as it is coordinated with the
            other inputs to this method. (Default: 0.08 assuming average 2020 US
            cost of natural gas in $/kWh with an efficiency of 0.75 with all burner
            and distribution losses).
        electricity_emissions: A number for the electric grid carbon emissions
            in kg CO2 per MWh. For locations in the USA, this can be obtained from
            he honeybee_energy.result.emissions future_electricity_emissions method.
            For locations outside of the USA where specific data is unavailable,
            the following rules of thumb may be used as a guide. (Default: 400).

            * 800 kg/MWh - for an inefficient coal or oil-dominated grid
            * 400 kg/MWh - for the US (energy mixed) grid around 2020
            * 100-200 kg/MWh - for grids with majority renewable/nuclear composition
            * 0-100 kg/MWh - for grids with renewables and storage

    Returns:
        A dictionary with several keys.

        -   proposed_eui -- A number for the total end use intensity. Specifically,
            this is the sum of all electricity, fuel, district heating/cooling,
            etc. divided by the gross floor area (including both conditioned
            and unconditioned spaces). Units are kWh/m2.

        -   proposed_energy -- A number for the total energy use of the proposed
            building in kWh.

        -   proposed_cost -- A number for the total annual energy cost of the
            proposed building.

        -   proposed_carbon -- A number for the total annual operational carbon
            emissions of the proposed building in kg of C02.
    """
    # get the energy use and floor area from the SQL
    total_floor_area, total_energy, total_cost, total_carbon = 0, 0, 0, 0
    # parse the SQL file
    sql_obj = SQLiteResult(sql_result)
    # get the total floor area of the model
    area_dict = sql_obj.tabular_data_by_name('Building Area')
    areas = tuple(area_dict.values())
    try:
        total_floor_area += areas[0][0]
    except IndexError:
        msg = 'Failed to find the "Building Area" table in the .sql file.'
        raise ValueError(msg)
    # get the energy use
    eui_dict = sql_obj.tabular_data_by_name('End Uses')
    for category, vals in eui_dict.items():
        try:
            vals = [float(v) for v in vals[:12]]
        except ValueError:
            break  # we hit the end of the table
        total_energy += sum(vals)
        total_cost += vals[0] * electricity_cost
        total_cost += vals[1] * natural_gas_cost
        total_cost += vals[10] * district_cooling_cost
        total_cost += vals[11] * district_heating_cost
        ele = (vals[0] * electricity_emissions) / 1000
        gas = (vals[1] * 277.358) / 1000
        dce = (vals[10] * (electricity_emissions / 3.5)) / 1000
        dhe = (vals[11] * 369.811) / 1000
        total_carbon += sum([ele, gas, dce, dhe])

    # put all metrics into a final dictionary
    result_dict = {
        'proposed_eui': round(total_energy / total_floor_area, 3),
        'proposed_energy': round(total_energy, 3),
        'proposed_cost': round(total_cost, 2),
        'proposed_carbon': round(total_carbon, 3)
    }
    return result_dict
