import util


raw = util.get_py_config_file_content(__file__)

# "_config" **MUST** be the first attribute

_config = "naive_predictor"

project_limit = 1000
topn = 1
order_factor = 0.0  # > 0: Consider the order of registering
