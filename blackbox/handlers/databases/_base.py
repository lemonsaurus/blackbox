from abc import abstractmethod
from pathlib import Path

from blackbox.handlers._base import BlackboxHandler


class BlackboxDatabase(BlackboxHandler):
    """An abstract database handler."""

    handler_type = "database"
    backup_extension = ""

    def __init__(self, **kwargs):
        """Set up database handler."""
        super().__init__(**kwargs)

        self.success = False  # Was the backup successful?
        self.output = ""      # What did the backup output?

    @abstractmethod
    def backup(self, backup_path: Path):
        """
        Back up a database to the provided backup Path.

        All subclasses must implement this method.
        """
        raise NotImplementedError

    @property
    def output(self):
        """Return sanitized output only."""
        return self.__output

    @output.setter
    def output(self, sensitive_output: str):
        """Set sanitized output."""
        self.__output = self.sanitize_output(sensitive_output)

    def get_id_for_retention(self) -> str:
        """Used for deleting only this kind of old backups."""
        return self.config.get("id")
