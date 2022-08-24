"""Module to parse End Use Intensity (EUI) from EnergyPlus results."""
import os
from collections import OrderedDict

from ladybug.sql import SQLiteResult


def eui_from_sql(sql_results):
    """Get a dictionary of End Use Intensity (EUI) results from EnergyPlus SQLs.

    Args:
        sql_results: The file path of the SQL result file that has been generated
            from an energy simulation. This can also be a list of SQL result files
            in which case EUI will be computed across all files. Lastly, it can
            be a directory or list of directories containing results, in which
            case, EUI will be calculated form all files ending in .sql.

    Returns:
        A dictionary with several keys.

        -   eui -- A number for the total end use intensity. Specifically,
            this is the sum of all electricity, fuel, district heating/cooling,
            etc. divided by the gross floor area (including both conditioned
            and unconditioned spaces). Units are kWh/m2.

        -   total_floor_area -- A number for the gross floor area of the building
            in m2. This excludes Rooms with True exclude_floor_area property.

        -   conditioned_floor_area -- A number for the conditioned floor area of the
            building in m2. This excludes Rooms with True exclude_floor_area property.

        -   total_energy -- A number for the total energy use of the building in kWh.

        -   end_uses -- A dictionary with the end use intensity for each of the end
            uses of the building (eg. heating, cooling, lighting, etc.).
    """
    # set initial values that will be computed based on results
    total_floor_area, conditioned_floor_area, total_energy = 0, 0, 0
    end_uses = OrderedDict()

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
                total_energy += total_use
                cat, sub_cat = category.split(':')
                eu_cat = cat if sub_cat == 'General' or sub_cat == 'Other' \
                    else sub_cat
                try:
                    end_uses[eu_cat] += total_use
                except KeyError:
                    end_uses[eu_cat] = total_use

    # assemble all of the results into a final dictionary
    result_dict = {
        'eui': round(total_energy / total_floor_area, 3),
        'total_floor_area': total_floor_area,
        'conditioned_floor_area': conditioned_floor_area,
        'total_energy': round(total_energy, 3)
    }
    result_dict['end_uses'] = OrderedDict(
        [(key, round(val / total_floor_area, 3)) for key, val in end_uses.items()]
    )
    return result_dict
