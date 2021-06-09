import gzip
import shutil
import tempfile
import typing
from abc import abstractmethod
from pathlib import Path

from blackbox.handlers._base import BlackboxHandler
from blackbox.utils.logger import log


# File suffixes considered as an archive
ARCHIVE_SUFFIXES = {".tar", ".zip"}


class BlackboxStorage(BlackboxHandler):
    """An abstract interface for creating Blackbox Storage Providers."""

    handler_type = "storage"

    def __init__(self, **kwargs):
        """Set up storage handler."""
        super().__init__(**kwargs)

        self.success = False  # Was the upload successful?
        self.output = ""     # What did the storage upload output?

    @staticmethod
    def compress(file_path: Path) -> tuple[typing.IO, bool]:
        """
        Compress the file using gzip into a tempfile.TemporaryFile.

        Returns a two elements tuple.
        The first one is a file-like object, which is removed when it is closed.
        The second one is True if the file has been recompressed, False otherwise.

        This should always be called before syncing the
        file to a storage provider.
        """
        # If the file is already considered as an archive, we don't recompress it
        if file_path.suffix in ARCHIVE_SUFFIXES:
            log.debug(f"File {file_path.name} is already compressed.")
            return open(file_path, "rb"), False

        temp_file = tempfile.NamedTemporaryFile(suffix=f"-{file_path.name}")

        log.debug(f"Compressing to temporary file: {temp_file.name}")
        with file_path.open(mode="rb") as f_in:
            with gzip.open(temp_file, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        temp_file.seek(0)
        return temp_file, True

    @abstractmethod
    def sync(self, file_path: Path):
        """
        Sync a file to a storage provider.

        All subclasses must implement this method.
        """
        raise NotImplementedError

    @abstractmethod
    def rotate(self, database_id: str):
        """
        Rotate the files in the storage provider.

        This deletes all files older than `rotation_days` days old, as long as
        those files fit certain regular expressions. We don't want to delete
        files that are not related to backup or logging.

        All subclasses must implement this method.
        """
        raise NotImplementedError
