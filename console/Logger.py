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
        if isinstance(msg, (unicode, str)):
            if not isinstance(msg, unicode):
                msg = msg.decode()

            self.cached.append(msg)

            if len(self.cached) >= 5:
                self.flush()

    def flush(self):
        if len(self.cached) > 0:
            event = LogEvent(log=u"".join(self.cached))
            wx.PostEvent(self.target, event)

            self.cached = []


class RedirectStdStreams(object):
    def __init__(self, stdout=None, stderr=None):
        if stdout:
            self._stdout = sys.stdout
            sys.stdout = stdout

        if stderr:
            self._stderr = sys.stderr
            sys.stderr = stderr

    def __del__(self):
        if hasattr(self, "_stdout"):
            sys.stdout.flush()
            sys.stdout = self._stdout

        if hasattr(self, "_stderr"):
            sys.stderr.flush()
            sys.stderr = self._stderr


class TextCtrlLogger(object):
    def __init__(self, logger_ctrl):
        self.logger_ctrl = logger_ctrl

    def set(self, msg):
        self.logger_ctrl.SetValue(msg)

    def append(self, msg):
        self.logger_ctrl.AppendText(msg)

    def clear(self):
        self.logger_ctrl.Clear()

    def is_empty(self):
        return self.logger_ctrl.IsEmpty()

    def go_to_end(self):
        self.logger_ctrl.SetInsertionPointEnd()
