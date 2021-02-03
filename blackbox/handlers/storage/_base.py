import gzip
import io
from abc import abstractmethod
from pathlib import Path

from blackbox.handlers._base import BlackboxHandler


class BlackboxStorage(BlackboxHandler):
    """An abstract interface for creating Blackbox Storage Providers."""

    def __init__(self, *args, **kwargs):
        """Set up database handler."""
        super().__init__(*args, **kwargs)
        self.success = False  # Was the sync successful?
        self.output = ""  # What did the sync/rotate output?

    @staticmethod
    def compress(file_path: Path) -> io.BytesIO:
        """
        Compress the file to gzip.

        This should always be called before syncing the
        file to a storage provider.
        """
        gzipped_bytes = gzip.compress(file_path.read_bytes())
        return io.BytesIO(gzipped_bytes)

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
