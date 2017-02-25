import util


raw = util.get_py_config_file_content(__file__)

# "_config" **MUST** be the first attribute

_config = "classifiers"

## topcoder, freelancer
dataset = "topcoder"
normalize_dataset = False

## 5, 10, 15, 20, 30
topn = 20

adjust_rec_list = False
rec_list_intact_length = 10

## NB, DTG, DTE, LR, MLP
classifier = "LR"

if classifier == "NB":
    normalize_dataset = False
elif classifier == "MLP":
    normalize_dataset = True
