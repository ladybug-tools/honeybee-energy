# coding=utf-8
"""Module for parsing EnergyPlus ZSZ csv result files into Ladybug DataCollections."""
from __future__ import division

from ladybug.futil import csv_to_matrix
from ladybug.datacollection import HourlyContinuousCollection
from ladybug.header import Header
from ladybug.analysisperiod import AnalysisPeriod
from ladybug.dt import Date
from ladybug.datatype.power import Power
from ladybug.datatype.massflowrate import MassFlowRate

import os
from datetime import datetime


class ZSZ(object):
    """Object for parsing EnergyPlus Zone Sizing (ZSZ) csv result files.

    Args:
        file_path: Full path to a ZSZ csv file that was generated by EnergyPlus.
        cooling_date: A ladybug Date object for the cooling design day. This is needed
            as the ZSZ file contains no information about the dates of the loads.
        heating_date: A ladybug Date object for the heating design day. This is needed
            as the ZSZ file contains no information about the dates of the loads.

    Properties:
        * file_path
        * cooling_date
        * heating_date
        * timestep
        * cooling_load_data
        * heating_load_data
        * cooling_flow_data
        * heating_flow_data
    """
    # a list if keywords to identify design day names from room names in headers
    DES_DAY_KEYWORDS = (' CLG ', ' HTG ', ' DESIGN DAY ')

    def __init__(self, file_path, cooling_date=Date(1, 1), heating_date=Date(1, 1)):
        """Initialize ZSZ"""
        # check that the file exists
        assert os.path.isfile(file_path), 'No file was found at {}'.format(file_path)
        assert file_path.endswith('.csv'), \
            '{} is not an CSV file ending in .csv.'.format(file_path)
        self._file_path = file_path

        # parse the data in the file
        data_mtx = csv_to_matrix(file_path)

        # extract the header and the peak values
        headers = data_mtx[0][:]  # copy the list
        del headers[0]
        peak = data_mtx[-3][:]  # copy the list
        del peak[0]
        del data_mtx[0]
        for i in range(3):
            del data_mtx[-1]
        self._headers = headers
        self._peak = peak

        # process the timestep of the data
        data_mtx = list(zip(*data_mtx))
        time1 = datetime.strptime(data_mtx[0][0], '%H:%M:%S')
        time2 = datetime.strptime(data_mtx[0][1], '%H:%M:%S')
        t_delta = time2 - time1
        self._timestep = int(3600 / t_delta.seconds)
        self._cooling_date = cooling_date
        self._heating_date = heating_date
        self._cool_a_period = AnalysisPeriod(
            cooling_date.month, cooling_date.day, 0,
            cooling_date.month, cooling_date.day, 23, timestep=self._timestep)
        self._heat_a_period = AnalysisPeriod(
            heating_date.month, heating_date.day, 0,
            heating_date.month, heating_date.day, 23, timestep=self._timestep)

        # process the body of the data
        del data_mtx[0]
        self._data = data_mtx

        # properties to be computed upon request
        self._cooling_load_data = None
        self._heating_load_data = None
        self._cooling_flow_data = None
        self._heating_flow_data = None

    @property
    def file_path(self):
        """Get the path to the .rdd file."""
        return self._file_path

    @property
    def cooling_date(self):
        """Get the date object assigned to the cooling design day."""
        return self._cooling_date

    @property
    def heating_date(self):
        """Get the date object assigned to the heating design day."""
        return self._heating_date

    @property
    def timestep(self):
        """Get the timestep of the data in the file."""
        return self._timestep

    @property
    def cooling_load_data(self):
        """Get a list of HourlyContinuousCollections for zone cooling load.

        There will be one data collection per conditioned zone in the model. Data
        collections are at the timestep of this object and values are in Watts.
        """
        if self._cooling_load_data is None:
            self._cooling_load_data = self._process_collections(
                'Summer Design Day Sensible Cooling Load', 'Des Sens Cool Load [W]', 'W')
        return self._cooling_load_data

    @property
    def heating_load_data(self):
        """Get a list of HourlyContinuousCollections for zone heating load.

        There will be one data collection per conditioned zone in the model. Data
        collections are at the timestep of this object and values are in Watts.
        """
        if self._heating_load_data is None:
            self._heating_load_data = self._process_collections(
                'Winter Design Day Heating Load', 'Des Heat Load [W]', 'W')
        return self._heating_load_data

    @property
    def cooling_flow_data(self):
        """Get a list of HourlyContinuousCollections for zone cooling mass flow.

        There will be one data collection per conditioned zone in the model. Data
        collections are at the timestep of this object and values are in m3/s.
        """
        if self._cooling_flow_data is None:
            self._cooling_flow_data = self._process_collections(
                'Summer Design Day Cooling Mass Flow',
                'Des Cool Mass Flow [kg/s]', 'kg/s')
        return self._cooling_flow_data

    @property
    def heating_flow_data(self):
        """Get a list of HourlyContinuousCollections for zone heating mass flow.

        There will be one data collection per conditioned zone in the model. Data
        collections are at the timestep of this object and values are in m3/s.
        """
        if self._heating_flow_data is None:
            self._heating_flow_data = self._process_collections(
                'Winter Design Day Heating Flow', 'Des Heat Mass Flow [kg/s]', 'kg/s')
        return self._heating_flow_data

    def _process_collections(self, description, data_type_text, unit):
        """Convert the raw data in the hidden _data property to data collections."""
        data_type = Power() if unit == 'W' else MassFlowRate()
        a_per = self._cool_a_period if 'Summer' in description else self._heat_a_period
        collections = []
        for i, col_head in enumerate(self._headers):
            if data_type_text in col_head:
                # try to differentiate the Zone name from the design day name
                c_head, zone_names, end_found = col_head.split(':')[:-1], [], False
                for name in c_head:
                    for kwrd in self.DES_DAY_KEYWORDS:
                        if kwrd in name:
                            end_found = True
                            break
                    else:
                        zone_names.append(name)
                    if end_found:
                        break
                if len(zone_names) == len(c_head):  # we did not find it
                    zone_name = c_head[0]
                else:
                    zone_name = ':'.join(zone_names)
                # create the header
                metadata = {'type': description, 'Zone': zone_name}
                head = Header(data_type, unit, a_per, metadata)
                collections.append(HourlyContinuousCollection(
                    head, [float(val) for val in self._data[i]]))
        return collections

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        return 'Energy ZSZ Result: {}'.format(self.file_path)
