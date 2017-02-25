from datetime import datetime
from time import mktime

import util


def _T(*t):
    return mktime(datetime(*t).timetuple())


raw = util.get_py_config_file_content(__file__)

# "_config" **MUST** be the first attribute

_config = "data_freelancer"

training_set_begin_date = _T(2016, 4, 1)
training_set_end_date = _T(2016, 8, 15)

training_set_limit = 3000
test_set_limit = 300

## 2, 3, 4, 5
win_times_threshold = 5
