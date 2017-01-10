import util


raw = util.get_py_config_file_content(__file__)

# "_config" **MUST** be the first attribute

_config = "clustering"

nb_clusters = 10
nb_fl_clusters = 10

fl_projects_limit = 20000
