def get_py_config_file_content(path):
    if path[-1] == 'c':
        path = path[:-1]

    raw = open(path).read().strip()
    return raw[raw.rindex("_config"):]
