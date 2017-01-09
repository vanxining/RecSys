from datetime import datetime
from time import mktime

import util


raw = util.get_py_config_file_content(__file__)

# "_config" **MUST** be the first attribute

_config = "data_freelancer"

training_set_begin_date = mktime(datetime(2015, 6, 1).timetuple())
training_set_end_date = mktime(datetime(2016, 8, 15).timetuple())

training_set_limit = 3000
test_set_limit = 300

win_times_threshold = 5
