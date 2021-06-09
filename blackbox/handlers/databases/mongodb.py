from blackbox.handlers.databases._base import BlackboxDatabase
from blackbox.utils import run_command
from blackbox.utils.logger import log


class MongoDB(BlackboxDatabase):
    """
    A Database handler that will do a mongodump for MongoDB, backing up all documents.

    This will use mongodump with --gzip and --archive, and must be restored using the same
    arguments, e.g. mongorestore --gzip --archive=/path/to/file.archive.
    """

    required_fields = ("connection_string",)
    backup_extension = ".archive"

    def backup(self, backup_path) -> None:
        """Dump all the data to a file and then return the filepath."""
        # Run the backup, and store the outcome in this object.
        self.success, self.output = run_command(
            f"mongodump "
            f"--uri={self.config['connection_string']} "
            "--gzip "
            "--forceTableScan "
            f"--archive={backup_path}"
        )
        log.debug(self.output)
