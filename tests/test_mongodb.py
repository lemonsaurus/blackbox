import pytest
import datetime
from pathlib import Path

def test_mongodb_backup(config_file, mocker, fake_process):
    """Test if the MongoDB database handler executes a backup"""

    from blackbox.handlers.databases import MongoDB

    mongo = MongoDB()

    date = datetime.datetime.today().strftime("%d_%m_%Y")
    archive = Path.home() / f"mongodb_blackbox_{date}.archive"

    command_to_run = [
            f"mongodump --uri= --gzip --forceTableScan --archive={archive}"
        ]

    fake_process.register_subprocess(
        command_to_run, stdout=["thing", "stuff"]
    )

    res = mongo.backup()

    assert res == archive
