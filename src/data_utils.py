def get_col_float(row_data, col, separator=','):
    """
    Tries to convert row_data at column position into float value, uses separator to split the row into columns.
    row_data - row of data to parse
    col - column to retrieve from row_data

    returns - tuple of (value, return_code) - value of col and True if succesfull, else 1.0 and False 
    """
    try:
        return (float(row_data.value.split(separator)[col].replace('"', '')), True)
    except Exception as e:
        print('data[{}] - conversion to float error: {}'.format(col, e))
        return (1.0, False)


def get_col_str(row_data, col, separator=','):
    return str(row_data.value.split(separator)[col])


def find_max_col_value(data, col):
    """
    Finds max value in column in given data and returns it
    """
    found_max, res = get_col_float(max(data, key=lambda x: get_col_float(x, col)[0]), col)
    return (found_max, res)

def col_values_sum(data, col):
    """
    Counts sum of given data values and returns it
    """
    total = 0
    for i in range(0, len(data)):
        value, res = get_col_float(data[i], col)
        total += value

    return total


