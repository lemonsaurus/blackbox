import inspect
import sys


class ImproperlyConfigured(Exception):
    """A class for raising configuration errors in our handlers."""
    def __init__(self, msg):
        try:
            ln = sys.exc_info()[-1].tb_lineno
        except AttributeError:
            ln = inspect.currentframe().f_back.f_lineno
        self.args = "ERROR: {2}".format(type(self), ln, msg),
        sys.exit(self)
