import datetime
import logging
import re
from pathlib import Path
from typing import Tuple

from config import BlackBox
from config.exceptions import ImproperlyConfigured
from databases._base import BlackBoxDatabase
from utils import run_command

log = logging.getLogger(__name__)


class Postgres(BlackBoxDatabase):
    enabled = BlackBox.postgres_enabled

    def __init__(self):
        """Prepare the database handler for use."""
        # Ensure the database is actually enabled.
        if not self.enabled:
            raise ImproperlyConfigured(
                "You cannot instantiate a database handler if that database is disabled. "
                "Please enable it in config.yaml first, and then try again."
            )

        # Ensure that the user has passed a connstring, and parse it.
        try:
            connstring = BlackBox.postgres_connstring
            self.user, self.password, self.host, self.port = self._parse_connstring(connstring)
        except (AttributeError, IndexError) as e:
            raise ImproperlyConfigured(
                "You must configure a proper connstring for the Postgres handler in your config.yaml! "
                f"Check the readme for more information"
            ) from e

        # Backup target
        date = datetime.date.today().strftime("%d_%m_%Y")
        self.backup_path = Path.home() / f"postgres_blackbox_{date}.sql"

    @staticmethod
    def _parse_connstring(connstring: str) -> Tuple[str, str, str, str]:
        """
        Parse a connstring and return user, password, host and port.

        The connstring has the following format:
        postgresql://user:password@host:port
        """
        return re.findall(r"postgres(?:ql)?://(.+):(.+)@(.+):(.+)", connstring)[0]

    def backup(self) -> Path:
        """Dump all the data to a file and then return the filepath."""
        output = run_command(
            f"pg_dumpall --file={self.backup_path}",
            PGUSER=self.user,
            PGPASSWORD=self.password,
            PGHOST=self.host,
            PGPORT=self.port,
        )
        print(output)
        log.debug(output)
        return self.backup_path
