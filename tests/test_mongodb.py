import datetime
from pathlib import Path

import pytest

from blackbox.exceptions import MissingFields
from blackbox.handlers.databases import MongoDB


@pytest.fixture
def mock_valid_mongodb_config():
    """Mock valid MongoDB config."""
    return {"connection_string": "mongodb://mongouser:mongopassword@host:port",
            "id": "main_mongo", }


@pytest.fixture
def mock_invalid_mongodb_config():
    """Mock invalid MongoDB config."""
    return {}


def test_mongodb_handler_can_be_instantiated_with_required_fields(
        mock_valid_mongodb_config):
    """Test if the MongoDB database handler can be instantiated."""
    MongoDB(**mock_valid_mongodb_config)


def test_mongodb_handler_fails_without_required_fields(
        mock_invalid_mongodb_config):
    """Test if the MongoDB database handler cannot be instantiated with missing fields."""
    with pytest.raises(MissingFields):
        MongoDB(**mock_invalid_mongodb_config)


def test_mongodb_backup(mock_valid_mongodb_config, fake_process):
    """Test if the MongoDB database handler executes a backup."""
    mongo = MongoDB(**mock_valid_mongodb_config)

    date = datetime.datetime.today().strftime("%d_%m_%Y")
    archive = Path.home() / f"main_mongo_blackbox_{date}.archive"

    command_to_run = [
        f"mongodump --uri=mongodb://mongouser:mongopassword@host:port --gzip --forceTableScan --archive={archive}"
    ]

    fake_process.register_subprocess(
        command_to_run, stdout=["thing", "stuff"]
    )

    res = mongo.backup()

    assert res == archive
