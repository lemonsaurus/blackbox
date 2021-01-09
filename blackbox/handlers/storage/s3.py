from pathlib import Path

from ._base import BlackboxStorage


class S3(BlackboxStorage):

    connstring_regex = r""
    valid_prefixes = []

    def sync(self, file_path: Path) -> None:
        """Sync a file to an S3 bucket."""
        raise NotImplementedError

    def rotate(self) -> None:
        """
        Rotate the files in the storage provider.

        This deletes all files older than `rotation_days` days old, as long as
        those files fit certain regular expressions. We don't want to delete
        files that are not related to backup or logging.
        """
        raise NotImplementedError
