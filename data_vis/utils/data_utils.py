# ©copyright Zdenek Dolezal 2024-, License GPL
# Utility functions for working with data

import math
import logging

logger = logging.getLogger("data_vis")


def find_axis_range(data, val_idx):
    """
    Finds range of data on index
    Parameters:
    data - data to find range in
    val_idx - idx where to access for data
    """
    return (
        min(data, key=lambda x: x[val_idx])[val_idx],
        max(data, key=lambda x: x[val_idx])[val_idx],
    )


def get_data_in_range(data, range_x):
    """
    Returns data in specified range
    Parameters:
    data - data to search in
    range_x - range of result data
    """
    return list(filter(lambda val: range_x[0] <= val[0] <= range_x[1], data))


def find_data_range(data, range_x, range_y=None):
    """
    Finds data value range in parameter data in space defined by range_x and range_yy
    data - data defined as list of lists, each row consist of [x, (y), top]
    range_x - bounds in x direction (min, max)
    range_y - bounds in y direction (min, max)

    returns - (min, max) of data
    """
    if range_y is None:
        filtered_data = list(
            filter(lambda row: range_x[0] <= row[0] <= range_x[1], data)
        )
    else:
        filtered_data = list(
            filter(
                lambda val: range_x[0] <= val[0] <= range_x[1]
                and range_y[0] <= val[1] <= range_y[1],
                data,
            )
        )
    top_index = 1 if range_y is None else 2
    return (
        min(filtered_data, key=lambda x: x[top_index])[top_index],
        max(filtered_data, key=lambda x: x[top_index])[top_index],
    )


def float_range(start, stop=None, step=None, precision=0.00001):
    """
    Generates range of float numbers like python range, but step can be float
    Inspiration taken from: https://pynative.com/python-range-for-float-numbers/
    start - start of interval
    stop - end of interval
    step - step size
    precision - comparison precision as fix to float comparison error
    returns - iterator from start to stop with step stepsize
    """
    val = start
    if stop is None:
        stop = start + 0.0
        val = 0.0

    if step is None:
        step = 1.0

    while True:
        if step > 0 and val - precision > stop:
            break
        elif step < 0 and val + precision < stop:
            break
        yield val
        val = val + step


def normalize_value(value, minimum, maximum):
    """
    Normalizes value into <0, 1> interval, range of data where value is included
    is specified by minimum and maximum
    """
    if math.isclose(maximum - minimum, 0):
        logger.error("Division by zero in normalize value!")
        return 1.0

    return (value - minimum) / (maximum - minimum)
