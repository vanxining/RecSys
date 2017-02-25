from datetime import datetime
from StringIO import StringIO


def get_current_timestamp():
    return datetime.now().strftime("%Y%m%d-%H%M%S")


class Logger(object):
    def __init__(self):
        self.sio = StringIO()

    def log(self, msg):
        print(msg)
        self.sio.write(msg + "\n")

    def save(self, fname):
        ts = get_current_timestamp()
        with open("results/%s-%s.log" % (ts, fname), "w") as outf:
            outf.write(self.sio.getvalue())
