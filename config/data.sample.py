from datetime import datetime

import util


def is_challenge_type_ok(challenge_type):
    if len(challenge_type_whitelist) == 0:
        return True

    return challenge_type in challenge_type_whitelist


raw = util.get_py_config_file_content(__file__)

# "_config" **MUST** be the first attribute

_config = "data"

year_from = 2015
end_date = datetime(2016, 4, 1)

## 1, 2, 3, 4, 5
win_times_threshold = 5

categorize_platech = True

# Code, First2Finish, Assembly Competition, Bug Hunt, UI Prototype Competition
challenge_type_whitelist = {"First2Finish", }
