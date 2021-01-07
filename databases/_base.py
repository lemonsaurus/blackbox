from abc import ABC, abstractmethod
from pathlib import Path

from blackbox.mixins import ConnstringParserMixin


class BlackboxDatabase(ABC, ConnstringParserMixin):
    """An abstract database handler."""

    def __init__(self):
        """Set up database handler."""
        super().__init__()
        self.success = None  # Was the backup successful?
        self.output = ""     # What did the backup output?

    @abstractmethod
    def backup(self) -> Path:
        """
        Back up a database and return the Path for the backup file.

        All subclasses must implement this method.
        """
        raise NotImplementedError
