import sys

# noinspection PyUnresolvedReferences
import newevent
# noinspection PyUnresolvedReferences
import wx


(LogEvent, EVT_LOG) = newevent.NewEvent()


class MyRedirector(object):
    def __init__(self, target):
        self.target = target
        self.cached = []

    def write(self, msg):
        if not isinstance(msg, unicode):
            msg = msg.decode()

        if msg:
            self.cached.append(msg)

    def flush(self):
        concated = "".join(self.cached)
        if concated:
            event = LogEvent(log=concated)
            wx.PostEvent(self.target, event)

        self.cached = []


# noinspection PyAbstractClass
class ListBoxLogger(object):
    def __init__(self, logger_ctrl):
        self.logger_ctrl = logger_ctrl

    def _count(self):
        return self.logger_ctrl.GetCount()

    def set(self, msg):
        self.clear()
        self.append(msg)

    def append(self, msg):
        lines = []
        for line in msg.split(u'\n'):
            if line:
                lines.append(line)

        if lines:
            self.logger_ctrl.InsertItems(lines, self._count())

    def clear(self):
        self.logger_ctrl.Clear()

    def is_empty(self):
        return self.logger_ctrl.IsEmpty()

    def go_to_end(self):
        if not self.is_empty():
            self.logger_ctrl.EnsureVisible(self._count() - 1)

    def select_all(self):
        for index in xrange(self._count()):
            self.logger_ctrl.Select(index)

    def get_selections(self):
        selections = []
        self.logger_ctrl.GetSelections(selections)

        logs = ""
        for index in selections:
            logs += self.logger_ctrl.GetString(index) + '\n'

        return logs[:-1] if logs else logs


class RedirectStdStreams(object):
    def __init__(self, stdout, stderr):
        self._stdout = sys.stdout
        self._stderr = sys.stderr

        sys.stdout = stdout
        sys.stderr = stderr

    def __del__(self):
        sys.stdout.flush()
        sys.stderr.flush()

        sys.stdout = self._stdout
        sys.stderr = self._stderr
