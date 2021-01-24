import sys


class ImproperlyConfigured(Exception):
    """A class for raising configuration errors in our handlers."""
    def __init__(self, msg):
        self.args = "ERROR: {0}".format(msg),
        sys.exit(self)
