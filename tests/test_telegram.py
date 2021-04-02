import pytest
import requests_mock

from blackbox.exceptions import MissingFields
from blackbox.handlers.notifiers import Telegram
from blackbox.utils.reports import Report, DatabaseReport, StorageReport


@pytest.fixture
def mock_valid_telegram_config():
    return {"token": "token", "chat_id": "007"}


@pytest.fixture
def mock_invalid_telegram_config():
    return {}


def test_telegram_handler_can_be_instantiated_with_required_fields(
        mock_valid_telegram_config):
    """Test if the telegram handler can be instantiated."""
    Telegram(**mock_valid_telegram_config)


def test_telegram_handler_fails_without_required_fields(
        mock_invalid_telegram_config):
    """
    Test if the telegram handler cannot be instantiated with missing fields.
    """
    with pytest.raises(MissingFields):
        Telegram(**mock_invalid_telegram_config)


def test_telegram_parse_report(mock_valid_telegram_config, report):
    """Test report parsing for Discord notifications"""

    telegram = Telegram(**mock_valid_telegram_config)
    telegram.report = report

    assert telegram._parse_report() == {'report': Report(databases=[
        DatabaseReport(database_id='main_mongo', success=True, output='salad',
                       storages=[StorageReport(storage_id='main_s3',
                                               success=True)])])}

