from datetime import datetime

import util


raw = util.get_py_config_file_content(__file__)

# "_config" **MUST** be the first attribute

_config = "collab_filtering"

nb_seeds = 1, 2, 4, 8

## 2014, 2015, 2016
year_from = 2016
end_date = datetime(2016, 6, 1)

## Naive, Cosine, Breese, Neighbor, Neighbor2, NeighborGlobal, Active
sim_func = "Active"
