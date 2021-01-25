import datetime
from pathlib import Path

import pytest

from blackbox.config import Blackbox
from blackbox.exceptions import ImproperlyConfigured
from blackbox.handlers.databases import Postgres


def test_postgres_handler_can_be_instantiated_with_one_connstring(config_file):
    """Test if the PostgreSQL database handler can be instantiated."""
    Postgres()


def test_postgres_fails_with_multiple_connstrings(config_file):
    """Test if the PostgreSQL database handler can not be instantiated with multiple connstrings."""

    # Insert one postgres config too many
    Blackbox.databases.append("postgres:/blabla")

    with pytest.raises(ImproperlyConfigured):
        Postgres()

    # Clean up
    Blackbox.databases.remove("postgres:/blabla")


def test_postgres_backup(config_file, mocker, fake_process):
    """Test if the Postgres database handler executes a backup"""

    postgres = Postgres()
    date = datetime.date.today().strftime("%d_%m_%Y")
    backup_path = Path.home() / f"postgres_blackbox_{date}.sql"

    command_to_run = [
        f"pg_dumpall --file={backup_path}"
    ]

    fake_process.register_subprocess(
        command_to_run, stdout=["thing", "stuff"]
    )

    res = postgres.backup()

    assert res == backup_path
