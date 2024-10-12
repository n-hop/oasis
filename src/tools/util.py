import os


def is_same_path(file_path1, file_path2):
    # check if file_path1 is the same as file_path2
    # return True if they are the same, otherwise False
    # file_path1 may contains `//`, remove them first
    file_path1 = os.path.normpath(file_path1)
    file_path2 = os.path.normpath(file_path2)
    if file_path1.endswith('/'):
        file_path1 = file_path1[:-1]
    if file_path2.endswith('/'):
        file_path2 = file_path2[:-1]
    return file_path1 == file_path2


def str_to_mbps(x, unit):
    ret = 0.00
    if unit == "K":
        ret = float(x) / 1000
    elif unit == "M":
        ret = float(x)
    elif unit == "G":
        ret = float(x) * 1000
    elif unit == "":
        ret = float(x) / 1000000
    return round(ret, 2)
