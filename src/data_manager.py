from enum import Enum


class DataType(Enum):
    Numerical = 0
    Categorical = 1


class DataManager:
    """
    Singleton that manages data access across the addon
    pattern design from https://python-3-patterns-idioms-test.readthedocs.io/en/latest/Singleton.html
    """
    class __DataManager:
        def __init__(self):
            self.raw_data = None
            self.parsed_data = None
            self.dimensions = 0

        def set_data(self, data):
            self.raw_data = data

        def get_raw_data(self):
            return self.raw_data

        def load_data(self, filepath, separator=','):
            self.parsed_data = None
            with open(filepath, 'r') as file:
                self.raw_data = [line.split(separator) for line in file]
                self.dimensions = len(self.raw_data[0])

        def get_parsed_data(self, data_type):
            if self.raw_data is None:
                print('No data has been loaded!')
                return [[]]

            self.parsed_data = []
            data = self.raw_data
            for row in data:
                self.parsed_data.append(self.__get_row_list(row, data_type))

            return self.parsed_data, first_line

        def __get_row_list(self, row, data_type):
            if data_type == DataType.Categorical:
                return [str(row[0]), float(row[1])]
            elif data_type == DataType.Numerical:
                return [float(x) for x in row]

        def get_data_range(self, col):
            ...

    instance = None

    def __new__(cls):
        if not DataManager.instance:
            DataManager.instance = DataManager.__DataManager()
        return DataManager.instance

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __setattr__(self, name):
        return setattr(self.instance, name)
