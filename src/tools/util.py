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


def is_base_path(file_path1, file_path2):
    """
    check whether `file_path1` is the base path of `file_path2`;
    for example: /root is base path of /root/a/b/c
    """
    file_path1 = os.path.normpath(file_path1)
    file_path2 = os.path.normpath(file_path2)
    if file_path1.endswith('/'):
        file_path1 = file_path1[:-1]
    if file_path2.endswith('/'):
        file_path2 = file_path2[:-1]
    return file_path2.startswith(file_path1)


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


def parse_test_file_name(test_file_path_string):
    """
    Parse the test YAML file string to extract the file path and test name.
    for example: `test.yaml:test1` will be parsed to `test.yaml` and `test1`

    return value: test_file_path, test_name
    """
    file = None
    temp_list = test_file_path_string.split(":")
    if len(temp_list) not in [1, 2]:
        return None, None
    if len(temp_list) == 2:
        file = temp_list[0]
        return file, temp_list[1]
    return test_file_path_string, None
