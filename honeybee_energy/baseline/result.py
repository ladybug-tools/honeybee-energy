"""Module for producing summaries of results from baseline simulations."""
from .pci import comparison_from_sql


def appendix_g_summary(
        proposed_sql, baseline_sqls, climate_zone, building_type='NonResidential',
        electricity_cost=0.12, natural_gas_cost=0.06,
        district_cooling_cost=0.04, district_heating_cost=0.08):
    """Get a dictionary with a summary of ASHRAE-90.1 Appendix G performance.

    Args:
        proposed_sql: The path of the SQL result file that has been generated from an
            energy simulation of a proposed building.
        baseline_sqls: The path of the SQL result file that has been generated from an
            energy simulation of a baseline building. This can also be a list of SQL
            result files (eg. for several simulations of different orientations)
            in which case the baseline performance will be computed as the average
            across all files. Lastly, it can be a directory or list of directories
            containing results, in which case, the average performance will be
            calculated form all files ending in .sql.
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

        -   baseline_eui -- A number for the baseline end use intensity. Specifically,
            this is the sum of all electricity, fuel, district heating/cooling,
            etc. divided by the gross floor area (including both conditioned
            and unconditioned spaces). Units are kWh/m2.

        -   baseline_energy -- A number for the total energy use of the baseline
            building in kWh.

        -   baseline_cost -- A number for the total annual energy cost of the
            baseline building.

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
    """
    # get the comparison report
    result_dict = comparison_from_sql(
        proposed_sql, baseline_sqls, climate_zone, building_type,
        electricity_cost, natural_gas_cost,
        district_cooling_cost, district_heating_cost)
    # remove all of the attributes that are not a part of Appendix G
    result_dict.pop('proposed_carbon')
    result_dict.pop('baseline_carbon')
    result_dict.pop('carbon_t_2016')
    result_dict.pop('carbon_t_2019')
    result_dict.pop('carbon_t_2022')
    result_dict.pop('pci_carbon')
    result_dict.pop('carbon_improvement_2016')
    result_dict.pop('carbon_improvement_2019')
    result_dict.pop('carbon_improvement_2022')
    return result_dict


def leed_v4_summary(
        proposed_sql, baseline_sqls, climate_zone, building_type='NonResidential',
        electricity_cost=0.12, natural_gas_cost=0.06, district_cooling_cost=0.04,
        district_heating_cost=0.08, electricity_emissions=400):
    """Get a dictionary with a summary of LEED v4 (and 4.1) performance.

    Args:
        proposed_sql: The path of the SQL result file that has been generated from an
            energy simulation of a proposed building.
        baseline_sqls: The path of the SQL result file that has been generated from an
            energy simulation of a baseline building. This can also be a list of SQL
            result files (eg. for several simulations of different orientations)
            in which case the baseline performance will be computed as the average
            across all files. Lastly, it can be a directory or list of directories
            containing results, in which case, the average performance will be
            calculated form all files ending in .sql.
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

        -   proposed_cost -- A number for the total annual energy cost of the
            proposed building.

        -   proposed_carbon -- A number for the total annual operational carbon
            emissions of the proposed building in kg of C02.

        -   baseline_eui -- A number for the baseline end use intensity. Specifically,
            this is the sum of all electricity, fuel, district heating/cooling,
            etc. divided by the gross floor area (including both conditioned
            and unconditioned spaces). Units are kWh/m2.

        -   baseline_cost -- A number for the total annual energy cost of the
            baseline building.

        -   baseline_carbon -- A number for the total annual operational carbon
            emissions of the baseline building in kg of C02.

        -   pci_target -- A fractional number for the target PCI for ASHRAE 90.1-2016.

        -   pci -- A fractional number for the PCI of the proposed building.

        -   pci_improvement -- A number less than 100 for the percentage better
            that the proposed building is over the target PCI for ASHRAE 90.1-2016.
            Negative numbers indicate a proposed building that is worse than
            the 2016 target PCI.

        -   carbon_target -- A fractional number for the target carbon index
            for ASHRAE 90.1-2016.

        -   carbon -- A fractional number for the performance improvement
            of the proposed building in terms of carbon emissions.

        -   carbon_improvement -- A number less than 100 for the percentage better
            that the proposed building is over the target carbon for ASHRAE 90.1-2016.
            Negative numbers indicate a proposed building that is worse than
            the 2016 target.

        -   leed_points -- An integer for the total number of LEED points that
            the proposed building would receive.
    """
    # get the comparison report
    result_dict = comparison_from_sql(
        proposed_sql, baseline_sqls, climate_zone, building_type,
        electricity_cost, natural_gas_cost,
        district_cooling_cost, district_heating_cost, electricity_emissions)
    # remove all of the attributes that are not a part of LEED v4
    result_dict.pop('proposed_energy')
    result_dict.pop('baseline_energy')
    result_dict.pop('pci_t_2019')
    result_dict.pop('pci_t_2022')
    result_dict.pop('pci_improvement_2019')
    result_dict.pop('pci_improvement_2022')
    result_dict.pop('carbon_t_2019')
    result_dict.pop('carbon_t_2022')
    result_dict.pop('carbon_improvement_2019')
    result_dict.pop('carbon_improvement_2022')
    # rename certain keys to make them clearer
    result_dict['pci_target'] = result_dict.pop('pci_t_2016')
    result_dict['pci_improvement'] = result_dict.pop('pci_improvement_2016')
    result_dict['carbon'] = result_dict.pop('pci_carbon')
    result_dict['carbon_target'] = result_dict.pop('carbon_t_2016')
    result_dict['carbon_improvement'] = result_dict.pop('carbon_improvement_2016')
    # compute the LEED points based on the other information
    healthcare = ('Hospital', 'Outpatient')
    schools = ('PrimarySchool', 'SecondarySchool')
    # compute the LEED points for energy cost
    pci_imp = result_dict['pci_improvement']
    cost_leed_pts = 0
    if building_type not in healthcare:  # use normal new construction
        if pci_imp >= 45:
            cost_leed_pts = 8 if building_type in schools else 9
        elif pci_imp >= 40:
            cost_leed_pts = 7 if building_type in schools else 8
        elif pci_imp >= 35:
            cost_leed_pts = 7
        elif pci_imp >= 30:
            cost_leed_pts = 6
        elif pci_imp >= 25:
            cost_leed_pts = 5
        elif pci_imp >= 20:
            cost_leed_pts = 4
        elif pci_imp >= 15:
            cost_leed_pts = 3
        elif pci_imp >= 10:
            cost_leed_pts = 2
        elif pci_imp >= 5:
            cost_leed_pts = 1
    else:
        if pci_imp >= 45:
            cost_leed_pts = 10
        elif pci_imp >= 40:
            cost_leed_pts = 9
        elif pci_imp >= 35:
            cost_leed_pts = 8
        elif pci_imp >= 30:
            cost_leed_pts = 7
        elif pci_imp >= 25:
            cost_leed_pts = 6
        elif pci_imp >= 20:
            cost_leed_pts = 5
        elif pci_imp >= 15:
            cost_leed_pts = 4
        elif pci_imp >= 10:
            cost_leed_pts = 3
        elif pci_imp >= 5:
            cost_leed_pts = 2
        elif pci_imp >= 2:
            cost_leed_pts = 1
    # compute the LEED points for carbon emissions
    c_imp = result_dict['carbon_improvement']
    carbon_leed_pts = 0
    if building_type not in healthcare:  # use normal new construction
        if c_imp >= 80:
            carbon_leed_pts = 8 if building_type in schools else 9
        elif c_imp >= 65:
            carbon_leed_pts = 7 if building_type in schools else 8
        elif c_imp >= 50:
            carbon_leed_pts = 7
        elif c_imp >= 40:
            carbon_leed_pts = 6
        elif c_imp >= 32:
            carbon_leed_pts = 5
        elif c_imp >= 24:
            carbon_leed_pts = 4
        elif c_imp >= 16:
            carbon_leed_pts = 3
        elif c_imp >= 10:
            carbon_leed_pts = 2
        elif c_imp >= 5:
            carbon_leed_pts = 1
    else:
        if c_imp >= 80:
            carbon_leed_pts = 10
        elif c_imp >= 65:
            carbon_leed_pts = 9
        elif c_imp >= 50:
            carbon_leed_pts = 8
        elif c_imp >= 40:
            carbon_leed_pts = 7
        elif c_imp >= 32:
            carbon_leed_pts = 6
        elif c_imp >= 24:
            carbon_leed_pts = 5
        elif c_imp >= 16:
            carbon_leed_pts = 4
        elif c_imp >= 10:
            carbon_leed_pts = 3
        elif c_imp >= 5:
            carbon_leed_pts = 2
        elif c_imp >= 2:
            carbon_leed_pts = 1
    result_dict['leed_points'] = cost_leed_pts + carbon_leed_pts
    return result_dict
