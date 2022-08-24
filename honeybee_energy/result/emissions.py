"""Module for converting EnergyPlus results into operational carbon emissions."""
import os
from collections import OrderedDict

from ladybug.sql import SQLiteResult


def emissions_region(location):
    """Get the region of carbon emissions associated with a location.

    Args:
        location: A ladybug Location object, which will be used to determine
            the subregion.

    Returns:
        A Tuple of text for the eGrid subregion for the location. The first value
        is the future emissions region, the second is the historical region,
        and the last is the historic hourly region. This will be None if
        the location cannot be mapped to a region.
    """
    # create the map from states to electric regions
    region_map = {
        'FL': ('FRCCc', 'FRCC', 'Florida'),
        'MS': ('SRMVc', 'SRMV', 'Midwest'),
        'NE': ('MROWc', 'MROW', 'Midwest'),
        'OR': ('NWPPc', 'NWPP', 'Northwest'),
        'CA': ('CAMXc', 'CAMX', 'California'),
        'VA': ('SRVCc', 'SRVC', 'Carolinas'),
        'AR': ('SRMVc', 'SRMV', 'Midwest'),
        'TX': ('ERCTc', 'ERCT', 'Texas'),
        'OH': ('RFCWc', 'RFCW', 'Midwest'),
        'UT': ('NWPPc', 'NWPP', 'Northwest'),
        'MT': ('NWPPc', 'NWPP', 'Northwest'),
        'TN': ('SRTVc', 'SRTV', 'Tennessee'),
        'ID': ('NWPPc', 'NWPP', 'Northwest'),
        'WI': ('MROEc', 'MROE', 'Midwest'),
        'WV': ('RFCWc', 'RFCW', 'Midwest'),
        'NC': ('SRVCc', 'SRVC', 'Carolinas'),
        'LA': ('SRMVc', 'SRMV', 'Midwest'),
        'IL': ('SRMWc', 'SRMW', 'Midwest'),
        'OK': ('SPSOc', 'SPSO', 'Central'),
        'IA': ('MROWc', 'MROW', 'Midwest'),
        'WA': ('NWPPc', 'NWPP', 'Northwest'),
        'SD': ('MROWc', 'MROW', 'Midwest'),
        'MN': ('MROWc', 'MROW', 'Midwest'),
        'KY': ('SRTVc', 'SRTV', 'Tennessee'),
        'MI': ('RFCMc', 'RFCM', 'Midwest'),
        'KS': ('SPNOc', 'SPNO', 'Central'),
        'NJ': ('RFCEc', 'RFCE', 'Mid-Atlantic'),
        'NY': ('NYSTc', 'NYCW', 'New York'),
        'IN': ('RFCWc', 'RFCW', 'Midwest'),
        'VT': ('NEWEc', 'NEWE', 'New England'),
        'NM': ('AZNMc', 'AZNM', 'Southwest'),
        'WY': ('RMPAc', 'RMPA', 'Rocky Mountains'),
        'GA': ('SRSOc', 'SRSO', 'SRSO'),
        'MO': ('SRMWc', 'SRMW', 'Midwest'),
        'DC': ('RFCEc', 'RFCE', 'Mid-Atlantic'),
        'SC': ('SRVCc', 'SRVC', 'Carolinas'),
        'PA': ('RFCEc', 'RFCE', 'Mid-Atlantic'),
        'CO': ('RMPAc', 'RMPA', 'Rocky Mountains'),
        'AZ': ('AZNMc', 'AZNM', 'Southwest'),
        'ME': ('NEWEc', 'NEWE', 'New England'),
        'AL': ('SRSOc', 'SRSO', 'Southeast'),
        'MD': ('RFCEc', 'RFCE', 'Mid-Atlantic'),
        'NH': ('NEWEc', 'NEWE', 'New England'),
        'MA': ('NEWEc', 'NEWE', 'New England'),
        'ND': ('MROWc', 'MROW', 'Midwest'),
        'NV': ('NWPPc', 'NWPP', 'Northwest'),
        'CT': ('NEWEc', 'NEWE', 'New England'),
        'DE': ('RFCEc', 'RFCE', 'Mid-Atlantic'),
        'RI': ('NEWEc', 'NEWE', 'New England')
    }
    # return the region
    try:
        return region_map[location.state]
    except KeyError:  # location could not be mapped to a region
        return None


def future_electricity_emissions(location, year=2030):
    """Get the future carbon emissions of the electric grid associated with a location.

    Args:
        location: A ladybug Location object, which will be used to determine
            the subregion.
        year: An integer for the future year for which carbon emissions will
            be estimated. Values must be an even number and be between 2020
            and 2050. (Default: 2030).

    Returns:
        A number for the electric grid carbon emissions in kg CO2 per MWh.
    """
    # create the map between regions, years, and carbon
    years = (2020, 2022, 2024, 2026, 2028, 2030, 2032, 2034,
             2036, 2038, 2040, 2042, 2044, 2046, 2048, 2050)
    region_map = {
        'AZNMc': (352, 412, 404, 389, 335, 301, 288, 279,
                  243, 208, 179, 182, 144, 136, 132, 126),
        'CAMXc': (212, 216, 198, 180, 159, 150, 147, 140,
                  130, 112, 101, 94, 82, 77, 75, 69),
        'ERCTc': (344, 342, 302, 302, 271, 208, 169, 158,
                  156, 141, 147, 128, 120, 105, 103, 88),
        'FRCCc': (368, 377, 381, 399, 355, 288, 273, 277,
                  268, 259, 251, 228, 192, 193, 190, 179),
        'MROEc': (411, 419, 411, 427, 389, 335, 285, 156,
                  149, 156, 146, 145, 121, 107, 122, 99),
        'MROWc': (375, 386, 354, 325, 298, 185, 149, 133,
                  127, 126, 129, 110, 88, 89, 79, 70),
        'NEWEc': (136, 148, 132, 108, 96, 81, 82, 70,
                  73, 67, 67, 58, 60, 59, 58, 59),
        'NWPPc': (177, 225, 185, 170, 148, 137, 138, 136,
                  135, 124, 111, 108, 103, 91, 87, 66),
        'NYSTc': (189, 206, 153, 134, 111, 92, 92, 79,
                  86, 83, 77, 78, 79, 78, 83, 83),
        'RFCEc': (276, 285, 254, 250, 238, 209, 206, 199,
                  203, 206, 198, 192, 187, 191, 170, 162),
        'RFCMc': (613, 634, 523, 527, 480, 393, 374, 357,
                  338, 319, 291, 287, 290, 227, 203, 156),
        'RFCWc': (493, 508, 467, 477, 463, 415, 390, 363,
                  335, 316, 287, 259, 242, 215, 217, 197),
        'RMPAc': (528, 580, 577, 584, 545, 444, 421, 354,
                  302, 301, 302, 259, 253, 194, 174, 168),
        'SPNOc': (461, 447, 249, 235, 228, 182, 162, 162,
                  156, 157, 155, 152, 117, 122, 130, 132),
        'SPSOc': (287, 277, 161, 143, 134, 119, 87, 82,
                  72, 64, 60, 56, 47, 49, 58, 56),
        'SRMVc': (421, 411, 358, 349, 329, 281, 269, 264,
                  253, 248, 241, 223, 206, 234, 233, 216),
        'SRMWc': (610, 637, 551, 542, 476, 366, 382, 366,
                  348, 335, 284, 246, 211, 187, 186, 175),
        'SRSOc': (334, 322, 327, 347, 263, 222, 206, 208,
                  207, 188, 185, 161, 145, 123, 126, 112),
        'SRTVc': (517, 554, 487, 513, 503, 408, 379, 355,
                  327, 325, 309, 281, 261, 230, 209, 176),
        'SRVCc': (293, 303, 301, 282, 259, 212, 203, 191,
                  188, 185, 179, 156, 149, 128, 121, 98),
    }
    # return the carbon intensity of electricity
    yr_i = years.index(year)
    region_str = emissions_region(location)
    if region_str is not None:
        return region_map[region_str[0]][yr_i]


def emissions_from_sql(sql_results, electricity_emissions):
    """Get a dictionary of Carbon Emissions Intensity results from EnergyPlus SQLs.

    This input emissions of electricity will be used to compute carbon intensity
    for both electricity and district heating/cooling. Fixed numbers will be used
    to convert the following on-site fuel sources:

    * Natural Gas --  277.358 kg/MWh
    * Propane -- 323.897 kg/MWh
    * Fuel Oil -- 294.962 kg/MWh

    Args:
        sql_results: The file path of the SQL result file that has been generated
            from an energy simulation. This can also be a list of SQL result files
            in which case EUI will be computed across all files. Lastly, it can
            be a directory or list of directories containing results, in which
            case, EUI will be calculated form all files ending in .sql.
        electricity_emissions: A number for the electric grid carbon emissions
            in kg CO2 per MWh. For locations in the USA, this can be
            obtained from the future_electricity_emissions method. For locations
            outside of the USA where specific data is unavailable, the following
            rules of thumb may be used as a guide:

            * 800 kg/MWh - for an inefficient coal or oil-dominated grid
            * 400 kg/MWh - for the US (energy mixed) grid around 2020
            * 100-200 kg/MWh - for grids with majority renewable/nuclear composition
            * 0-100 kg/MWh - for grids with renewables and storage

    Returns:
        A dictionary with several keys.

        -   carbon_intensity -- A number for the total annual carbon intensity.
            This is the sum of all operational carbon emissions divided by the
            gross floor area (including both conditioned and unconditioned spaces).
            Units are kg CO2/m2.

        -   total_floor_area -- A number for the gross floor area of the building
            in m2. This excludes Rooms with True exclude_floor_area property.

        -   conditioned_floor_area -- A number for the conditioned floor area of the
            building in m2. This excludes Rooms with True exclude_floor_area property.

        -   total_carbon -- A number for the total annual operational carbon
            in kg of Co2.

        -   end_uses -- A dictionary with the carbon intensity for each of the end
            uses of the building (eg. heating, cooling, lighting, etc.).

        -   sources -- A dictionary with the carbon intensity for each of the energy
            sources of the building (eg. electricity, natural_gas, district_heat, etc.).
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

    # set initial values that will be computed based on results
    total_floor_area, conditioned_floor_area = 0, 0
    tot_elec, tot_gas, tot_pro, tot_oil, tot_heat, tot_cool = 0, 0, 0, 0, 0, 0
    end_uses = OrderedDict()

    # loop through the sql files and add the energy use
    for sql_path in sql_paths:
        # parse the SQL file
        sql_obj = SQLiteResult(sql_path)
        # get the total floor area of the model
        area_dict = sql_obj.tabular_data_by_name('Building Area')
        areas = tuple(area_dict.values())
        total_floor_area += areas[0][0]
        conditioned_floor_area += areas[1][0]
        # get the energy use
        eui_dict = sql_obj.tabular_data_by_name('End Uses By Subcategory')
        for category, vals in eui_dict.items():
            total_use = sum([val for val in vals[:12]])
            if total_use != 0:
                elec = (vals[0] * electricity_emissions) / 1000
                gas = (vals[1] * 277.358) / 1000
                pro = (vals[7] * 323.897) / 1000
                oil = (vals[6] * 294.962) / 1000
                heat = (vals[11] * electricity_emissions) / 1000
                cool = (vals[10] * electricity_emissions) / 1000

                tot_elec += elec
                tot_gas += gas
                tot_pro += pro
                tot_oil += oil
                tot_heat += heat
                tot_cool += cool
                carb = sum((elec, gas, pro, oil, heat, cool))

                cat, sub_cat = category.split(':')
                eu_cat = cat if sub_cat == 'General' or sub_cat == 'Other' \
                    else sub_cat
                try:
                    end_uses[eu_cat] += carb
                except KeyError:
                    end_uses[eu_cat] = carb

    # compute the total carbon emissions
    sources = OrderedDict([
        ('electricity', tot_elec),
        ('natural_gas', tot_gas),
        ('propane', tot_pro),
        ('oil', tot_oil),
        ('district_heat', tot_heat),
        ('district_cool', tot_cool)
    ])
    total_carbon = sum(sources.values())

    # assemble all of the results into a final dictionary
    result_dict = {
        'carbon_intensity': round(total_carbon / total_floor_area, 3),
        'total_floor_area': total_floor_area,
        'conditioned_floor_area': conditioned_floor_area,
        'total_carbon': round(total_carbon, 3)
    }
    result_dict['end_uses'] = OrderedDict(
        [(key, round(val / total_floor_area, 3)) for key, val in end_uses.items()]
    )
    result_dict['sources'] = OrderedDict(
        [(key, round(val / total_floor_area, 3)) for key, val in sources.items()
         if val != 0]
    )
    return result_dict
