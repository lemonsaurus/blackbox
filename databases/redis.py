from pathlib import Path

from databases._base import BlackBoxDatabase


class Redis(BlackBoxDatabase):

    def _get_connstring(self):
        """Try to get the connstring out of the config."""
        raise NotImplementedError

    def _parse_connstring(self):
        """Parse the connstring and return its constituent parts."""
        raise NotImplementedError

    def backup(self) -> Path:
        raise NotImplementedError
