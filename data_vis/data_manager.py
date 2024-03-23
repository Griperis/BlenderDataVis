# File: data_manager.py
# Author: Zdenek Dolezal
# Licence: GPL 3.0
# Description: Data loading, data analysis and data information interface

import os
import numpy as np
import csv
import typing
import logging
logger = logging.getLogger("data_vis")

from enum import Enum


class DataType(Enum):
    Numerical = 0
    Categorical = 1
    Invalid = 2


class DataSubtype(Enum):
    XY = 0
    XY_Anim = 1
    XYW = 2
    XYZ = 3
    XYZ_Anim = 4
    XYZW = 5


class ChartData:
    '''V3.0 abstraction of data access, simpler to use'''
    def __init__(self, parsed_data, labels: typing.Optional[typing.List[str]] = None):
        self.parsed_data = np.array(parsed_data)
        self.lines = len(parsed_data)
        self.labels = labels


class DataManager:
    '''
    Singleton that manages data access across the addon
    pattern design from https://python-3-patterns-idioms-test.readthedocs.io/en/latest/Singleton.html
    '''
    class __DataManager:

        def __init__(self):
            self.default_state()

        def default_state(self):
            self.raw_data = None
            self.parsed_data = None
            self.predicted_data_type = None
            self.has_labels = False
            self.lines = 0
            self.dimensions = 0
            self.ranges = {}
            self.filepath = ''
            self.tail_length = 0
            self.animable = False

        def set_data(self, data):
            self.raw_data = data

        def get_raw_data(self):
            return self.raw_data

        def load_data(self, filepath, delimiter=','):
            if not os.path.exists(filepath):
                return 0

            self.default_state()
            self.filepath = filepath
            try:
                with open(filepath, 'r', encoding='UTF-8') as file:
                    csv_reader = csv.reader(file, delimiter=delimiter)
                    self.raw_data = []
                    for line in csv_reader:
                        if len(line) == 0:
                            continue
                        self.raw_data.append(line)
                self.analyse_data()
                self.parse_data()
            except UnicodeDecodeError as e:
                self.predicted_data_type = DataType.Invalid
                return 0
            
            if self.predicted_data_type == DataType.Invalid:
                return 0
            
            return len(self.raw_data)

        def analyse_data(self):
            '''Analyses data type and labels'''
            total = 0
            for i, col in enumerate(self.raw_data[0]):
                try:
                    row = float(col)
                except Exception as e:
                    total += 1

            if total == len(self.raw_data[0]):
                self.has_labels = True

            prev_row_info = {}
            row_info = None
            for i in range(1, len(self.raw_data)):
                row_info = {'floats': 0, 'strings': 0, 'first_string': False}
                row = self.raw_data[1]
                for j, col in enumerate(row):
                    try:
                        float(col)
                        row_info['floats'] += 1
                    except Exception as e:
                        if j == 0:
                            row_info['first_string'] = True
                        row_info['strings'] += 1

                if prev_row_info and prev_row_info != row_info:
                    logger.error('Invalid entry: {}: {}'.format(i), row)
                    self.predicted_data_type = DataType.Invalid
                prev_row_info = row_info

            if row_info is None:
                self.predicted_data_type = DataType.Invalid

            if self.predicted_data_type != DataType.Invalid:
                if row_info['first_string'] and row_info['strings'] == 1 and row_info['floats'] > 0:
                    self.dimensions = 2
                    if row_info['floats'] > 1:
                        self.animable = True
                    self.predicted_data_type = DataType.Categorical
                elif row_info['strings'] == 0 and row_info['floats'] >= 2:
                    if row_info['floats'] == 2 or row_info['floats'] == 3:
                        self.dimensions = row_info['floats']
                        self.animable = False
                    elif row_info['floats'] >= 3:
                        self.dimensions = 3
                        self.animable = True
                    self.predicted_data_type = DataType.Numerical
                else:
                    self.predicted_data_type = DataType.Invalid

                self.tail_length = row_info['floats'] - self.dimensions
                self.__calculate_subtypes()

        def parse_data(self):
            '''Takes raw_data and parses it into parsed_data while finding data ranges'''
            if self.raw_data is None:
                logger.warning('No data has been loaded!')
                self.parsed_data = [[]]
                return

            if self.predicted_data_type == DataType.Invalid:
                logger.error('Invalid data loaded!')
                self.parsed_data = [[]]
                return

            self.parsed_data = []
            data = self.raw_data

            if self.has_labels:
                self.labels = tuple(str(x) for x in self.raw_data[0])
                start_idx = 1
            else:
                start_idx = 0

            min_max = []
            self.lines = 0
            for i in range(start_idx, len(data)):
                self.lines += 1
                row_list = self.__get_row_list(self.raw_data[i])
                if i == start_idx:
                    min_max = [[val, val] for val in row_list]
                else:
                    for j, val in enumerate(row_list):
                        if val < min_max[j][0]:
                            min_max[j][0] = val

                        if val > min_max[j][1]:
                            min_max[j][1] = val
             
                self.parsed_data.append(row_list)
   
            self.ranges['x'] = min_max[0]
            if len(min_max) == 2 or self.predicted_data_type == DataType.Categorical:
                self.ranges['z'] = min_max[1]
            elif len(min_max) > 2:
                self.ranges['y'] = min_max[1]
                self.ranges['z'] = min_max[2]
                if len(min_max) == 3:
                    self.ranges['w'] = min_max[2]
                if len(min_max) >= 4:
                    self.ranges['w'] = min_max[3]

            if self.animable:
                z_ranges = min_max[len(self.ranges) - 1:]
                if self.dimensions == 3 and self.tail_length == 1:
                    self.ranges['z_anim'] = self.__merge_ranges(self.ranges['w'], self.ranges['z'])
                else:
                    self.ranges['z_anim'] = [min(z_ranges, key=lambda x: x[0])[0], max(z_ranges, key=lambda x: x[1])[1]]

            if self.predicted_data_type == DataType.Categorical:
                self.ranges['x'] = (0, len(self.parsed_data) - 1)

        def get_parsed_data(self, subtype=None):
            if subtype:
                if subtype == DataSubtype.XY:
                    return self.parsed_data
                elif subtype == DataSubtype.XYW:
                    if len(self.parsed_data[0]) != 3:
                        return [[x[0], x[1], x[2]] for x in self.parsed_data]
                    else:
                        return self.parsed_data
                elif subtype == DataSubtype.XY_Anim:
                    raise NotImplementedError()
                elif subtype == DataSubtype.XYZ:
                    return self.parsed_data
                elif subtype == DataSubtype.XYZW:
                    if len(self.parsed_data[0]) != 4:
                        return [[x[0], x[1], x[2], x[3]] for x in self.parsed_data]
                    else:
                        return self.parsed_data
                elif subtype == DataSubtype.XYZ_Anim:
                    raise NotImplementedError()
            else:
                return self.parsed_data

        def get_chart_data(self) -> typing.Optional[ChartData]:
            if self.raw_data is None:
                return None
            return ChartData(self.parsed_data, self.labels if self.has_labels else [])

        def get_labels(self):
            return self.labels

        def get_range(self, axis, subtype=None):
            if axis == 'z_anim' and 'z_anim' not in self.ranges:
                raise RuntimeError('looking for z anim and z anim is not found')
            if axis in self.ranges:
                return tuple(self.ranges[axis])
            else:
                return (0.0, 1.0)
        
        def get_step_size(self, axis):
            default_steps = 10
            if axis in self.ranges:
                ax_range = tuple(self.ranges[axis])
                return (ax_range[1] - ax_range[0]) / default_steps
            else:
                return 1.0

        def get_filename(self):
            return os.path.split(self.filepath)[1]

        def override(self, data_type, dims):
            if data_type != self.predicted_data_type or dims != self.dimensions:
                if data_type == DataType.Categorical:
                    self.ranges['x'] = (0, len(self.parsed_data) - 1)
                else:
                    if dims == 2 and self.dimensions == 3:
                        self.ranges['z'] = self.ranges['y']
                    #self.parse_data()
                return True
            else:
                return False

        def get_dimensions(self):
            return self.dimensions if self.dimensions <= 3 else 3

        def get_possible_subtypes(self):
            return self.subtypes

        def has_compatible_subtype(self, subtypes):
            '''Checks whether data have at least one of chart supported subtypes'''
            if not isinstance(subtypes, (list, tuple)):
                raise ValueError('Subtypes have to be in list')
            # at least one matches, variatons are decided by chart code
            return len(set(self.subtypes).intersection(set(subtypes))) > 0

        def has_subtype(self, subtype):
            '''Checks whether subtype is in possible subtypes for data'''
            return subtype in self.get_possible_subtypes()

        def is_type(self, data_type, min_dims, only_3d=False, only_2d=False):
            if isinstance(min_dims, (list, tuple)):
                min_dims = min(min_dims) # TODO Argument fixture
            if only_3d and self.dimensions < 3:
                return False
            if only_2d and self.dimensions < 2:
                return False
            return data_type == self.predicted_data_type and min_dims <= self.dimensions

        def print_data(self, nice=True):
            if not nice:
                print(self.parsed_data)
            else:
                for row in self.parsed_data:
                    print(row)

        def __get_row_list(self, row):
            if self.predicted_data_type == DataType.Categorical:
                ret_list = [str(row[0])]
                ret_list.extend([float(x) for x in row[1:]])
                return ret_list
            elif self.predicted_data_type == DataType.Numerical:
                return [float(x) for x in row]

        def __calculate_subtypes(self):
            self.subtypes = []
            if self.dimensions == 2:
                self.subtypes.append(DataSubtype.XY)
            if self.dimensions == 3:
                self.subtypes += [DataSubtype.XY_Anim, DataSubtype.XYZ, DataSubtype.XYW]
            if self.dimensions == 3 and self.tail_length >= 1:
                self.subtypes += [DataSubtype.XYZ_Anim, DataSubtype.XYZW]

        def __merge_ranges(self, first, second):
            return (min(first[0], second[0]), max(first[1], second[1]))

        def __str__(self):
            return '{}\nSUBTYPES: {}\nL: {}\nNOFL: {}\nDIMS: {}\nRNGS: {}\nANIM_DATA: {}\nANIM: {}'.format(
                self.predicted_data_type,
                self.subtypes,
                self.has_labels,
                self.lines,
                self.dimensions,
                self.ranges,
                self.tail_length,
                self.animable
            )

    instance = None

    def __new__(cls):
        if not DataManager.instance:
            DataManager.instance = DataManager.__DataManager()
        return DataManager.instance

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __setattr__(self, name):
        return setattr(self.instance, name)
