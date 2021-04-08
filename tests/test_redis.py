import datetime
from pathlib import Path

import pytest

from blackbox.exceptions import MissingFields
from blackbox.handlers.databases import Redis


@pytest.fixture
def mock_valid_redis_config():
    """Mock valid Redis config."""
    return {"password": "citrus", "host": "localhost", "port": "5432",
            "id": "main_redis", }


@pytest.fixture
def mock_invalid_redis_config():
    """Mock invalid Redis config."""
    return {"password": "limoncello"}


def test_can_be_instantiated_with_required_fields(mock_valid_redis_config):
    """Test if the redis database handler can be instantiated."""
    Redis(**mock_valid_redis_config)


def test_fails_without_required_fields(mock_invalid_redis_config):
    """Test if the redis database handler cannot be instantiated with missing fields."""
    with pytest.raises(MissingFields):
        Redis(**mock_invalid_redis_config)


def test_redis_backup(mock_valid_redis_config, fake_process):
    """Test if the redis database handler executes a backup."""
    redis = Redis(**mock_valid_redis_config)

    date = datetime.date.today().strftime("%d_%m_%Y")
    backup_path = Path.home() / f"main_redis_blackbox_{date}.rdb"

    command_to_run = [
        f"redis-cli -h {redis.config.get('host')} -p {redis.config.get('port')} --rdb {backup_path}"
    ]

    fake_process.register_subprocess(
        command_to_run, stdout=["redis backup"]
    )

    res = redis.backup()

    assert res == backup_path
