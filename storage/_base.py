from abc import abstractmethod
from pathlib import Path

from blackbox.abc import BlackboxConnstringParser


class BlackboxStorageProvider(BlackboxConnstringParser):
    @abstractmethod
    def sync(self, file_path: Path):
        """
        Sync a file to a storage provider.

        All subclasses must implement this method.
        """
        raise NotImplementedError

    @abstractmethod
    def rotate(self):
        """
        Rotate the files in the storage provider.

        This deletes all files older than `rotation_days` days old, as long as
        those files fit certain regular expressions. We don't want to delete
        files that are not related to backup or logging.

        All subclasses must implement this method.
        """
        raise NotImplementedError
