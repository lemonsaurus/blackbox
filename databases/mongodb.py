from pathlib import Path

from config import BlackBox
from databases._base import BlackBoxDatabase
from utils import run_command


class MongoDB(BlackBoxDatabase):

    def _get_connstring(self):
        """Try to get the connstring out of the config."""
        raise NotImplementedError

    def _parse_connstring(self):
        """Parse the connstring and return its constituent parts."""
        raise NotImplementedError

    def backup(self) -> Path:
        raise NotImplementedError
