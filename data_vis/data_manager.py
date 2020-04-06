from enum import Enum
import bpy


class DataType(Enum):
    Numerical = 0
    Categorical = 1
    Invalid = 2


class DataManager:
    """
    Singleton that manages data access across the addon
    pattern design from https://python-3-patterns-idioms-test.readthedocs.io/en/latest/Singleton.html
    """
    class __DataManager:

        def __init__(self):
            self.raw_data = None
            self.parsed_data = None
            self.predicted_data_type = None
            self.has_labels = False
            self.labels = ()
            self.dimensions = 0
            self.ranges = {}

        def set_data(self, data):
            self.raw_data = data

        def get_raw_data(self):
            return self.raw_data

        def load_data(self, filepath, separator=','):
            self.__init__()
            try:
                with open(filepath, 'r') as file:
                    self.raw_data = []
                    for line in file:
                        if line == '\n':
                            continue
                        self.raw_data.append(line.split(separator))
                        
                self.analyse_data()
            except UnicodeDecodeError as e:
                self.predicted_data_type = DataType.Invalid
                return 0
            
            return len(self.raw_data)

        def analyse_data(self):
            total = 0
            for i, col in enumerate(self.raw_data[0]):
                try:
                    row = float(col)
                except Exception as e:
                    total += 1

            if total == len(self.raw_data[0]):
                self.has_labels = True

            prev_row_info = {}
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
                    print('Invalid entry: {}: {}'.format(i), row)
                    self.predicted_data_type = DataType.Invalid
                prev_row_info = row_info

            if self.predicted_data_type != DataType.Invalid:
                if row_info['first_string'] and row_info['strings'] == 1 and row_info['floats'] > 0:
                    self.predicted_data_type = DataType.Categorical
                elif row_info['strings'] == 0 and row_info['floats'] >= 2:
                    self.predicted_data_type = DataType.Numerical
                else:
                    self.predicted_data_type = DataType.Invalid

                self.parse_data()

            self.dimensions = len(self.raw_data[0])

        def parse_data(self):
            if self.raw_data is None:
                print('No data has been loaded!')
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
            for i in range(start_idx, len(data)):
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
            if len(min_max) == 2:
                self.ranges['z'] = min_max[1]
            if len(min_max) > 2:
                self.ranges['y'] = min_max[1]
                self.ranges['z'] = min_max[2]
            
            if self.predicted_data_type == DataType.Categorical:
                self.ranges['x'] = (0, len(self.parsed_data) - 1)

        def get_parsed_data(self):
            return self.parsed_data

        def get_labels(self):
            return self.labels

        def get_range(self, axis):
            if axis in self.ranges:
                return tuple(self.ranges[axis])
            else:
                return (0.0, 1.0)
        
        def override(self, data_type, dims):
            if data_type != self.predicted_data_type or dims != self.dimensions:
                if data_type == DataType.Categorical:
                    self.ranges['x'] = (0, len(self.parsed_data) - 1)
                else:
                    self.parse_data()
                return True
            else:
                return False

        def is_type(self, data_type, dims):
            return data_type == self.predicted_data_type and self.dimensions in dims

        def __get_row_list(self, row):
            if self.predicted_data_type == DataType.Categorical:
                return [str(row[0]), float(row[1])]
            elif self.predicted_data_type == DataType.Numerical:
                return [float(x) for x in row]

    instance = None

    def __new__(cls):
        if not DataManager.instance:
            DataManager.instance = DataManager.__DataManager()
        return DataManager.instance

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __setattr__(self, name):
        return setattr(self.instance, name)
