import datetime
from pathlib import Path

from blackbox.handlers.databases import Redis


def test_redis_handler_can_be_instantiated(config_file):
    """Test if the Redis database handler can be instantiated."""

    Redis()


def test_redis_backup(config_file, mocker, fake_process):
    """Test if the redis database handler executes a backup"""

    redis = Redis()

    date = datetime.date.today().strftime("%d_%m_%Y")
    backup_path = Path.home() / f"redis_blackbox_{date}.rdb"

    command_to_run = [
        f"redis-cli -h {redis.config.get('host')} -p {redis.config.get('port')} --rdb {backup_path}"
        # redis-cli -h password@host              -p  port                      --rdb C:\Users\Inveracity\redis_blackbox_25_01_2021.rdb'
    ]

    fake_process.register_subprocess(
        command_to_run, stdout=["redis backup"]
    )

    res = redis.backup()

    assert res == backup_path
