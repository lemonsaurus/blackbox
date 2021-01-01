from pathlib import Path

from databases._base import BlackboxDatabase


class MongoDB(BlackboxDatabase):

    def _get_connstring(self):
        """Ensure we only have a single connstring configured, and return it."""
        raise NotImplementedError

    def _parse_connstring(self):
        """Parse the connstring and return its constituent parts."""
        raise NotImplementedError

    def backup(self) -> Path:
        raise NotImplementedError
