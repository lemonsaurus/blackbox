import datetime
from pathlib import Path

import pytest

from blackbox.exceptions import MissingFields
from blackbox.handlers.databases import Postgres


@pytest.fixture
def mock_valid_postgres_config():
    return {"username": "lemon", "password": "citrus", "host": "localhost",
            "port": "5432", "id": "main_postgres", }


@pytest.fixture
def mock_invalid_postgres_config():
    return {"username": "lime"}


def test_postgres_handler_can_be_instantiated_with_required_fields(
        mock_valid_postgres_config):
    """Test if the PostgreSQL database handler can be instantiated."""
    Postgres(**mock_valid_postgres_config)


def test_postgres_handler_fails_without_required_fields(
        mock_invalid_postgres_config):
    """Test if the PostgreSQL database handler cannot be instantiated with missing fields."""
    with pytest.raises(MissingFields):
        Postgres(**mock_invalid_postgres_config)


def test_postgres_backup(mock_valid_postgres_config, fake_process):
    """Test if the Postgres database handler executes a backup"""

    postgres = Postgres(**mock_valid_postgres_config)
    date = datetime.date.today().strftime("%d_%m_%Y")
    backup_path = Path.home() / f"main_postgres_blackbox_{date}.sql"

    command_to_run = [
        f"pg_dumpall --file={backup_path}"
    ]

    fake_process.register_subprocess(
        command_to_run, stdout=["thing", "stuff"]
    )

    res = postgres.backup()

    assert res == backup_path
