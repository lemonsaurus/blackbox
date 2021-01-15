import datetime
import logging
from pathlib import Path

from _base import BlackboxDatabase
from blackbox.utils import run_command

log = logging.getLogger(__name__)


class Postgres(BlackboxDatabase):
    """A Database handler that will do a pg_dumpall for Postgres, backing up all tables."""

    connstring_regex = r"postgres(?:ql)?://(?P<user>.+):(?P<password>.+)@(?P<host>.+):(?P<port>.+)"
    valid_prefixes = [
        "postgres",
        "postgresql",
    ]

    def backup(self) -> Path:
        """Dump all the data to a file and then return the filepath."""
        date = datetime.date.today().strftime("%d_%m_%Y")
        backup_path = Path.home() / f"postgres_blackbox_{date}.sql"

        # Run the backup, and store the outcome.
        self.success, self.output = run_command(
            f"pg_dumpall --file={backup_path}",
            PGUSER=self.config.get("user"),
            PGPASSWORD=self.config.get("password"),
            PGHOST=self.config.get("host"),
            PGPORT=self.config.get("port"),
        )
        log.debug(self.output)

        # Return the path to the backup file
        return backup_path
