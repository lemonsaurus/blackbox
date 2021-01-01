from abc import abstractmethod
from pathlib import Path

from blackbox.abc import BlackboxConnstringParser


class BlackboxDatabase(BlackboxConnstringParser):
    """An abstract database handler."""

    @abstractmethod
    def backup(self) -> Path:
        """
        Back up a database and return the Path for the backup file.

        All subclasses must implement this method.
        """
        raise NotImplementedError
