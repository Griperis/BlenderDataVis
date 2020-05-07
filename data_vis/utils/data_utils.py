# File: data_utils.py
# Author: Zdenek Dolezal
# Licence: GPL 3.0
# Description: Utility functions for working with data

from data_vis.data_manager import DataType


def find_axis_range(data, val_idx):
    '''
    Finds range of data on index
    Parameters:
    data - data to find range in
    val_idx - idx where to access for data
    '''
    return (min(data, key=lambda x: x[val_idx])[val_idx], max(data, key=lambda x: x[val_idx])[val_idx])


def get_data_in_range(data, range_x):
    '''
    Returns data in specified range
    Parameters:
    data - data to search in
    range_x - range of result data
    '''
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
    if maximum - minimum == 0:
        print('Division by zero in normalize value!')
        return 1.0
    return (value - minimum) / (maximum - minimum)
