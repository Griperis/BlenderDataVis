from enum import Enum


class DataType(Enum):
    Numerical = 0
    Categorical = 1
    Categorical_3D = 2


def get_row_list(row_data, data_type, separator):
    if data_type == DataType.Categorical:
        row = row_data.value.split(separator)
        return [str(row[0]), float(row[1])]
    elif data_type == DataType.Numerical:
        return [float(x) for x in row_data.value.split(separator)]


def get_data_as_ll(data, data_type, separator=','):
    mat = []
    for row in data:
        mat.append(get_row_list(row, data_type, separator))
    return mat


def find_axis_range(data, val_idx):
    return (min(data, key=lambda x: x[val_idx])[val_idx], max(data, key=lambda x: x[val_idx])[val_idx])


def get_data_in_range(data, range_x):
    return list(filter(lambda val: range_x[0] <= val[0] <= range_x[1], data))


def find_data_range(data, range_x, range_y=None):
    '''
    Finds data value range in parameter data in space defined by range_x and range_yy
    data - data defined as list of lists, each row consist of [x, (y), top]
    range_x - bounds in x direction (min, max)
    range_y - bounds in y direction (min, max)

    returns - (min, max) of data
    '''
    if range_y is None:
        filtered_data = list(filter(lambda row: range_x[0] <= row[0] <= range_x[1], data))
    else:
        filtered_data = list(filter(lambda val: range_x[0] <= val[0] <= range_x[1] and range_y[0] <= val[1] <= range_y[1], data))

    top_index = (1 if range_y is None else 2)
    return (min(filtered_data, key=lambda x: x[top_index])[top_index], max(filtered_data, key=lambda x: x[top_index])[top_index])


def get_col_float(row_data, col, separator=','):
    '''
    Tries to convert row_data at column position into float value, uses separator to split the row into columns.
    row_data - row of data to parse
    col - column to retrieve from row_data

    returns - tuple of (value, return_code) - value of col and True if succesfull, else 1.0 and False 
    '''
    try:
        return (float(row_data.value.split(separator)[col].replace('"', '')), True)
    except Exception as e:
        print('data[{}] - conversion to float error: {}'.format(col, e))
        return (1.0, False)


def get_col_str(row_data, col, separator=','):
    return str(row_data.value.split(separator)[col])


def col_values_min(data, col, start=0, nof=0):
    '''
    Finds min value in column in given data and returns it
    '''
    if start >= len(data) or start + nof > len(data):
        raise IndexError('Out of data bounds!')
    if nof == 0:
        nof = len(data)

    found_min, res = get_col_float(min(data[start:start + nof], key=lambda x: get_col_float(x, col)[0]), col)
    return (found_min, res)


def col_values_max(data, col, start=0, nof=0):
    '''
    Finds max value in column in given data and returns it
    '''
    if start >= len(data) or start + nof > len(data):
        raise IndexError('NOF > Length of data!')
    if nof == 0:
        nof = len(data)
    found_max, res = get_col_float(max(data[start:start + nof], key=lambda x: get_col_float(x, col)[0]), col)
    return (found_max, res)


def col_values_min_max(data, col, start=0, nof=0):
    '''
    Finds min and max value in column in given data and returns it
    '''
    found_max, _ = col_values_max(data, col, start, nof)
    found_min, _ = col_values_min(data, col, start, nof)
    return (found_min, found_max)


def col_values_sum(data, col):
    '''
    Counts sum of given data values and returns it
    '''
    total = 0
    for i in range(0, len(data)):
        value, res = get_col_float(data[i], col)
        total += value

    return total


def float_data_gen(data, col, label_col, separator=','):
    '''
    Creates generator from data entry saved in blender data
    data - data to create generator from
    col - column, where are values
    label_col - column for label values
    '''
    for i, entry in enumerate(data):
        val, res = get_col_float(entry, col, separator)
        label = get_col_str(entry, label_col, separator)
        yield {'val': val, 'label': label, 'res': res}


def float_range(start, stop=None, step=None):
    '''
    Generates range of float numbers like python range, but step can be float
    Inspiration taken from: https://pynative.com/python-range-for-float-numbers/
    '''
    if stop is None:
        stop = start + 0.0
        start = 0.0

    if step is None:
        step = 1.0

    while True:
        if step > 0 and start > stop:
            break
        elif step < 0 and start < stop:
            break
        yield start
        start = start + step


def normalize_value(value, minimum, maximum):
    '''
    Normalizes value into <0, 1> interval, range of data where value is included
    is specified by minimum and maximum
    '''
    return (value - minimum) / (maximum - minimum)
