from pathlib import Path

from storage._base import BlackboxStorageProvider


class GoogleDrive(BlackboxStorageProvider):

    def _get_connstring(self):
        """Ensure we only have a single connstring configured, and return it."""
        raise NotImplementedError

    def _parse_connstring(self):
        """Parse the connstring and return its constituent parts."""
        raise NotImplementedError

    def sync(self, file_path: Path) -> None:
        """Sync a file to Google Drive."""
        raise NotImplementedError

    def rotate(self) -> None:
        """
        Rotate the files in the storage provider.

        This deletes all files older than `rotation_days` days old, as long as
        those files fit certain regular expressions. We don't want to delete
        files that are not related to backup or logging.
        """
        raise NotImplementedError
