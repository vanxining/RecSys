from datetime import datetime
from time import mktime


training_set_begin_date = mktime(datetime(2015, 6, 1).timetuple())
training_set_end_date = mktime(datetime(2016, 8, 15).timetuple())

training_set_limit = 3000
test_set_limit = 300

win_times_threshold = 5
