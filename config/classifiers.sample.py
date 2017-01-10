import util


raw = util.get_py_config_file_content(__file__)

# "_config" **MUST** be the first attribute

_config = "classifiers"

dataset = "topcoder"
normalize_dataset = False

topn = 30

adjust_rec_list = True
rec_list_intact_length = 5

# NB, LR, MLP
classifier = "LR"

if classifier == "MLP":
    normalize_dataset = True
