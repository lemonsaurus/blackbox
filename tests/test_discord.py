import pytest
import requests_mock

from blackbox.exceptions import MissingFields
from blackbox.handlers.notifiers.discord import Discord


WEBHOOK = "https://discord.com/api/webhooks/x"


@pytest.fixture
def mock_valid_discord_config():
    """Mock valid Discord config."""
    return {"webhook": WEBHOOK}


@pytest.fixture
def mock_invalid_discord_config():
    """Mock invalid Discord config."""
    return {}


def test_discord_handler_can_be_instantiated_with_required_fields(mock_valid_discord_config):
    """Test if the discord notifier handler can be instantiated."""
    Discord(**mock_valid_discord_config)


def test_discord_handler_fails_without_required_fields(mock_invalid_discord_config):
    """Test if the discord notifier handler cannot be instantiated with missing fields."""
    with pytest.raises(MissingFields):
        Discord(**mock_invalid_discord_config)


def test_discord_notify(mock_valid_discord_config, report):
    """Test report parsing for Discord notifications."""
    discord = Discord(**mock_valid_discord_config)
    discord.report = report

    assert discord._parse_report() == {
        'avatar_url': 'https://raw.githubusercontent.com/lemonsaurus/blackbox/main/img/blackbox_avatar.png',  # NOQA: E501
        'content': None,
        'embeds': [{'color': 1024049,
                    'fields': [{'inline': True,
                                'name': '**main_mongo**',
                                'value': ':white_check_mark:  main_s3'}],
                    'title': 'Backup'}],
        'username': 'blackbox'
    }

    with requests_mock.Mocker() as m:
        m.post(WEBHOOK)
        discord.notify()


def test_discord_uses_1024_character_limit():
    """Test that Discord specifically uses 1024 character limit."""
    from blackbox.utils.reports import DatabaseReport
    from blackbox.utils.reports import Report

    discord = Discord(webhook=WEBHOOK)

    # Verify Discord's character limit is set correctly
    assert discord.max_output_chars == 1024

    # Create a failed database with output longer than 1024 chars
    long_output = "Error: " + "x" * 2000
    failed_db = DatabaseReport("failed_db", False, long_output)

    report = Report()
    report.databases = [failed_db]
    discord.report = report

    optimized_output = discord.get_optimized_output()

    # Should be truncated to Discord's 1024 character limit
    assert len(optimized_output) <= 1024


def test_discord_failed_output_excludes_successful_databases():
    """Test that output only includes failed databases, not successful ones."""
    from blackbox.utils.reports import DatabaseReport
    from blackbox.utils.reports import Report

    discord = Discord(webhook=WEBHOOK)

    # Mix of successful and failed databases
    success_db = DatabaseReport("success_db", True, "Success log content")
    failed_db = DatabaseReport("failed_db", False, "Error occurred")

    report = Report()
    report.databases = [success_db, failed_db]
    discord.report = report

    # Since failed_db.success is False, report.success will be False automatically
    # because Report.success returns True only if ALL databases succeeded
    parsed = discord._parse_report()

    # Output field should only contain failed database output
    output_field = next(
        field for field in parsed["embeds"][0]["fields"]
        if field["name"] == "Output"
    )
    assert "Error occurred" in output_field["value"]
    assert "Success log content" not in output_field["value"]
