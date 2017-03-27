from datetime import datetime
from time import mktime

import util


def _T(*t):
    return mktime(datetime(*t).timetuple())


raw = util.get_py_config_file_content(__file__)

# "_config" **MUST** be the first attribute

_config = "cf"

## topcoder, freelancer
dataset = "topcoder"

nb_seeds = 1, 2, 3, 4

topcoder_begin_date = datetime(2016, 1, 1)
topcoder_end_date = datetime(2016, 6, 1)

# Code, First2Finish, Assembly Competition, Bug Hunt, UI Prototype Competition
topcoder_challenge_type_whitelist = {"First2Finish",}

freelancer_begin_date = _T(2016, 11, 25)
freelancer_end_date = _T(2016, 12, 12)

# The project must contain all the required technologies
# An empty list/tuple/set is OK
# Examples: (3,), (20,), (17,)
freelancer_tech_requirement = (20,)

## Naive, Cosine, Breese, Neighbor, Neighbor2, NeighborGlobal, Active
sim_func = "Active"
