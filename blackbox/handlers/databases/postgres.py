from blackbox.handlers.databases._base import BlackboxDatabase
from blackbox.utils import run_command
from blackbox.utils.logger import log


class Postgres(BlackboxDatabase):
    """A Database handler that will do a pg_dumpall for Postgres, backing up all tables."""

    required_fields = ("username", "password", "host", )
    backup_extension = ".sql"

    def backup(self, backup_path) -> None:
        """Dump all the data to a file and then return the filepath."""
        # Run the backup, and store the outcome.
        self.success, self.output = run_command(
            f"pg_dumpall --file={backup_path}",
            PGUSER=self.config["username"],
            PGPASSWORD=self.config["password"],
            PGHOST=self.config["host"],
            PGPORT=str(self.config.get("port", "5432")),
        )
        log.debug(self.output)
