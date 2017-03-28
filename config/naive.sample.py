import util


raw = util.get_py_config_file_content(__file__)

# "_config" **MUST** be the first attribute

_config = "naive_predictor"

## topcoder, freelancer
dataset = "topcoder"

project_limit = 1000

## 1, 2, 3
topn = 1

# > 0: Consider the order of registering
order_factor = 0.0
