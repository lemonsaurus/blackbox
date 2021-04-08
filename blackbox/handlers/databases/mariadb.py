import datetime
from pathlib import Path

from blackbox.handlers.databases._base import BlackboxDatabase
from blackbox.utils import run_command
from blackbox.utils.logger import log


class MariaDB(BlackboxDatabase):
    """
    A Database handler that will do a mysqldump for MariaDB, backing up all tables.
    """

    required_fields = ("username", "password", "host", )

    def backup(self) -> Path:
        """Dump all the data to a file and then return the filepath."""
        date = datetime.date.today().strftime("%d_%m_%Y")

        user = self.config["username"]
        password = self.config["password"]
        host = self.config["host"]
        port = str(self.config.get("port", "3306"))

        backup_path = Path.home() / f"{self.config['id']}_blackbox_{date}.sql"

        # Run the backup, and store the outcome.
        self.success, self.output = run_command(
            f"mysqldump -h {host} -u {user} --password='{password}' "
            f"--port={port} --all-databases > {backup_path}"
        )
        log.debug(self.output)
        # Explicitly check if error message is occurred.
        # Somehow mysqldump is always successful.
        if "error" in self.output.lower():
            self.success = False
            log.debug("mysqldump has error(s) in log")

        # Return the path to the backup file
        return backup_path
