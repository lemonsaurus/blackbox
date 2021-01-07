import datetime
import logging
from pathlib import Path

from databases._base import BlackboxDatabase
from utils import run_command

log = logging.getLogger(__name__)


class MongoDB(BlackboxDatabase):
    """
    A Database handler that will do a mongodump for MongoDB, backing up all documents.

    This will use mongodump with --gzip and --archive, and must be restored using the same
    arguments, e.g. mongorestore --gzip --archive=/path/to/file.archive.
    """

    connstring_regex = r"mongodb://(?P<user>.+):(?P<password>.+)@(?P<host>.+):(?P<port>.+)"
    valid_uri_protocols = [
        "mongodb"
    ]

    def backup(self) -> Path:
        """Dump all the data to a file and then return the filepath."""
        date = datetime.date.today().strftime("%d_%m_%Y")
        archive_file = Path.home() / f"mongodb_blackbox_{date}.archive"
        output = run_command(
            f"mongodump "
            f"--uri={self.connstring} "
            "--gzip "
            "--forceTableScan "
            f"--archive={archive_file}"
        )
        log.debug(output)
        return archive_file
