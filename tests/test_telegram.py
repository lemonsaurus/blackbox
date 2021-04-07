import pytest

from blackbox.exceptions import MissingFields
from blackbox.handlers.notifiers import Telegram


@pytest.fixture
def mock_valid_telegram_config():
    return {"token": "token", "chat_id": "007"}


@pytest.fixture
def mock_invalid_telegram_config():
    return {}


def test_can_be_instantiated_with_required_fields(mock_valid_telegram_config):
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

    assert telegram._parse_report() == 'Blackbox Backup Status:\n' \
                                       'main_mongo: \n✅ main_s3\n'
