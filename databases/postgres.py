import datetime
import logging
import re
from pathlib import Path
from typing import Optional, Tuple

from blackbox import Blackbox
from blackbox.exceptions import ImproperlyConfigured
from databases._base import BlackboxDatabase
from utils import run_command

log = logging.getLogger(__name__)


class Postgres(BlackboxDatabase):
    """A Database handler that will do a pg_dumpall for Postgres, backing up all tables."""

    def __init__(self):
        """Prepare the database handler for use."""
        # Ensure the database is actually enabled.
        if not self.enabled:
            raise ImproperlyConfigured(
                "You cannot instantiate a database handler if that database is disabled. "
                "Please enable it in config.yaml first, and then try again."
            )

        # Ensure that the user configured a single, valid connstring
        try:
            self.user, self.password, self.host, self.port = self._parse_connstring()
        except (AttributeError, IndexError) as e:
            raise ImproperlyConfigured(
                "You must configure a proper connstring for the Postgres handler in your config.yaml! "
                f"Check the readme for more information"
            ) from e

        # Backup target
        date = datetime.date.today().strftime("%d_%m_%Y")
        self.backup_path = Path.home() / f"postgres_blackbox_{date}.sql"

    def _get_connstring(self):
        """Ensure we only have a single connstring configured, and return it."""
        connstrings = [connstring for connstring in Blackbox.databases if connstring.startswith("postgres")]

        # No connstrings configured
        if len(connstrings) == 0:
            return None

        # More than one connstring configured! Fail hard.
        elif len(connstrings) > 1:
            raise ImproperlyConfigured(
                "You cannot configure more than one Postgres connstring at a time!"
            )

        # If only a single connstring is configured, return it!
        return connstrings[0]

    def _parse_connstring(self) -> Optional[Tuple[str, str, str, str]]:
        """
        Parse a connstring and return user, password, host and port.

        The connstring has the following format:
        postgresql://user:password@host:port
        """

        return re.findall(r"postgres(?:ql)?://(.+):(.+)@(.+):(.+)", self._get_connstring())[0]

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
