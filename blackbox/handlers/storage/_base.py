import gzip
import shutil
import tempfile
import typing
from abc import abstractmethod
from pathlib import Path

from blackbox.handlers._base import BlackboxHandler
from blackbox.utils.logger import log


class BlackboxStorage(BlackboxHandler):
    """An abstract interface for creating Blackbox Storage Providers."""

    @staticmethod
    def compress(file_path: Path) -> typing.IO:
        """
        Compresses the file using gzip into a tempfile.TemporaryFile.

        Returns a file-like object, which is removed when it is closed.
        This should always be called before syncing the
        file to a storage provider.
        """
        temp_file = tempfile.NamedTemporaryFile(suffix=f"-{file_path.name}")

        log.debug(f"Compressing to temporary file: {temp_file.name}")
        with file_path.open(mode="rb") as f_in:
            with gzip.open(temp_file, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        temp_file.seek(0)
        return temp_file

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
