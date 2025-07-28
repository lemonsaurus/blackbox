import pytest

from blackbox.exceptions import MissingFields
from blackbox.handlers.notifiers import Telegram


@pytest.fixture
def mock_valid_telegram_config():
    """Mock valid telegram config."""
    return {"token": "token", "chat_id": "007"}


@pytest.fixture
def mock_invalid_telegram_config():
    """Mock invalid telegram config."""
    return {}


def test_can_be_instantiated_with_required_fields(mock_valid_telegram_config):
    """Test if the telegram handler can be instantiated."""
    Telegram(**mock_valid_telegram_config)


def test_fails_without_required_fields(mock_invalid_telegram_config):
    """Test if the telegram handler cannot be instantiated with missing fields."""
    with pytest.raises(MissingFields):
        Telegram(**mock_invalid_telegram_config)


def test_parse_report(mock_valid_telegram_config, report):
    """Test report parsing for telegram notifications."""
    telegram = Telegram(**mock_valid_telegram_config)
    telegram.report = report

    assert telegram._parse_report() == 'Blackbox Backup Status:\nmain_mongo: \n✅ main_s3\n'


def test_telegram_uses_4096_character_limit():
    """Test that Telegram specifically uses 4096 character limit."""
    from blackbox.utils.reports import DatabaseReport
    from blackbox.utils.reports import Report

    telegram = Telegram(token="test_token", chat_id="12345")
    
    # Verify Telegram's character limit is set correctly
    assert telegram.max_output_chars == 4096
    
    # Create a failed database with output longer than 4096 chars
    long_output = "Error: " + "x" * 5000
    failed_db = DatabaseReport("failed_db", False, long_output)
    
    report = Report()
    report.databases = [failed_db]
    telegram.report = report
    
    optimized_output = telegram.get_optimized_output()
    
    # Should be truncated to Telegram's 4096 character limit
    assert len(optimized_output) <= 4096
