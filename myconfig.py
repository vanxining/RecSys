import ConfigParser
from datetime import datetime


class MyConfig(object):
    def __init__(self):
        self.raw = ""

    def open(self, fname):
        config = ConfigParser.RawConfigParser()

        with open(fname, "r") as inf:
            self.raw = inf.read().strip()
            inf.seek(0)
            config.readfp(inf, fname)

        return config


def parse_date(date_str):
    return datetime(*[int(i) for i in date_str.split('-')])


def get_current_timestamp():
    return datetime.now().strftime("%Y%m%d-%H%M%S")
