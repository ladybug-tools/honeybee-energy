"""Module to parse on-site electricity generation from EnergyPlus results."""
import os
from ladybug.sql import SQLiteResult


def generation_summary_from_sql(sql_results):
    """Get a dictionary of electricity generation results from EnergyPlus SQLs.

    Args:
        sql_results: The file path of the SQL result file that has been generated
            from an energy simulation. This can also be a list of SQL result files
            in which case electricity generation will be computed across all files.
            Lastly, it can be a directory or list of directories containing results,
            in which case, electricity generation will be calculated form all files
            ending in .sql.

    Returns:
        A dictionary with several keys.

        -   total_production -- A positive number for the total electricity
            produced on-site by all generators. Units are kWh.

        -   total_consumption -- A negative number for the total electricity
            consumed on-site by all end uses. Units are kWh.

        -   production_used_on_site -- A positive number for the total electricity
            produced on-site that was also consumed on-site. Units are kWh.

        -   production_surplus_sold -- A positive number for the total electricity
            produced on-site that was sold to the electric utility as it could
            not be used on-site. Units are kWh.

        -   consumption_purchased -- A negative number for the total electricity
            that was purchased from the electric utility as there was no on-site
            power at the time to meet the energy consumption demand. Units are kWh.
    """
    # set initial values that will be computed based on results
    total_production, total_consumption = 0, 0
    production_surplus_sold, consumption_purchased = 0, 0

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

    # loop through the sql files and add the energy production / consumption
    for sql_path in sql_paths:
        # parse the SQL file
        sql_obj = SQLiteResult(sql_path)
        # get the energy use
        gen_dict = sql_obj.tabular_data_by_name('Electric Loads Satisfied')
        for category, vals in gen_dict.items():
            if category == 'Total On-Site Electric Sources':
                total_production += vals[0]
            elif category == 'Total Electricity End Uses':
                total_consumption += vals[0]
            elif category == 'Electricity Coming From Utility':
                consumption_purchased += vals[0]
            elif category == 'Surplus Electricity Going To Utility':
                production_surplus_sold += vals[0]

    # assemble all of the results into a final dictionary
    result_dict = {
        'total_production': round(total_production, 3),
        'total_consumption': round(-total_consumption, 3),
        'production_used_on_site': round(total_production - production_surplus_sold),
        'production_surplus_sold': round(production_surplus_sold, 3),
        'consumption_purchased': round(-consumption_purchased, 3)
    }
    return result_dict


def generation_data_from_sql(sql_results):
    """Get a data collections of electricity production and consumption.

    Args:
        sql_results: The file path of the SQL result file that has been generated
            from an energy simulation. This can also be a list of SQL result files
            in which case electricity generation will be computed across all files.
            Lastly, it can be a directory or list of directories containing results,
            in which case, electricity generation will be calculated form all files
            ending in .sql.

    Returns:
        A tuple with two values.

        -   production -- A data collection of the total electricity produced on-site
            by all generators. Values are in kWh. Will be None if no outputs
            related to electricity production were requested from the simulation.

        -   consumption -- A data collection of the total electricity consumed
            by all end uses. Values are in kWh. Will be None if no outputs related
            to electricity production were requested from the simulation.
    """
    prod_data, net_data = [], []

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

    # loop through the sql files and add the energy production / consumption
    for sql_path in sql_paths:
        # parse the SQL file
        sql_obj = SQLiteResult(sql_path)
        sql_prod = sql_obj.data_collections_by_output_name(
            'Facility Total Produced Electricity Energy')
        prod_data.extend(sql_prod)
        sql_net = sql_obj.data_collections_by_output_name(
            'Facility Net Purchased Electricity Energy')
        net_data.extend(sql_net)

    # sum the production data together
    if len(net_data) == 0:
        return None, None
    elif isinstance(net_data[0], (float, int)):  # annual total of data
        production = sum(prod_data)
    else:
        if len(prod_data) == 0:
            production = net_data[0].duplicate()
            production.values = [0] * len(production)
        elif len(prod_data) == 1:
            production = prod_data[0]
        else:
            production = prod_data[0]
            for data_i in prod_data[1:]:
                production = production + data_i
        production.header.metadata['System'] = 'Whole Building'
        production.header.metadata['type'] = 'Electricity Production'

    # compute the electricity consumption from the net data
    if len(net_data) == 1:
        consumption = net_data[0] + production
    else:
        consumption = net_data[0]
        for data_i in net_data[1:]:
            consumption = consumption + data_i
        consumption = consumption + production
    try:
        consumption.header.metadata['type'] = 'Electricity Consumption'
    except AttributeError:  # annual total of data
        pass

    return production, consumption
