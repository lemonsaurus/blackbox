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


def test_discord_output_optimization_single_failure():
    """Test output optimization for a single failed database."""
    from blackbox.utils.reports import DatabaseReport
    from blackbox.utils.reports import Report

    discord = Discord(webhook=WEBHOOK)

    # Create a failed database with long output
    long_output = "Error line " + "x" * 2000  # Much longer than 1024
    failed_db = DatabaseReport("failed_db", False, long_output)

    report = Report()
    report.databases = [failed_db]
    discord.report = report

    optimized_output = discord._get_optimized_output()

    # Should be truncated to last 1024 characters
    assert len(optimized_output) <= 1024
    assert optimized_output.endswith("x" * 1000)  # Should be tail of the output


def test_discord_output_optimization_multiple_failures():
    """Test output optimization for multiple failed databases."""
    from blackbox.utils.reports import DatabaseReport
    from blackbox.utils.reports import Report

    discord = Discord(webhook=WEBHOOK)

    # Create multiple failed databases with different output lengths
    db1 = DatabaseReport("db1", False, "Short error")
    db2 = DatabaseReport("db2", False, "Medium " + "x" * 100)
    db3 = DatabaseReport("db3", False, "Very long error " + "y" * 2000)

    report = Report()
    report.databases = [db1, db2, db3]
    discord.report = report

    optimized_output = discord._get_optimized_output()

    # Should be within 1024 character limit
    assert len(optimized_output) <= 1024
    # Should contain all database IDs
    assert "db1:" in optimized_output
    assert "db2:" in optimized_output
    assert "db3:" in optimized_output


def test_discord_output_optimization_no_failures():
    """Test output optimization when no databases failed."""
    from blackbox.utils.reports import DatabaseReport
    from blackbox.utils.reports import Report

    discord = Discord(webhook=WEBHOOK)

    # Create successful databases only
    success_db = DatabaseReport("success_db", True, "All good")

    report = Report()
    report.databases = [success_db]
    discord.report = report

    optimized_output = discord._get_optimized_output()

    # Should be empty since no failures
    assert optimized_output == ""


def test_discord_output_tail_truncation():
    """Test that output uses tail (last 10 lines) of logs."""
    from blackbox.utils.reports import DatabaseReport
    from blackbox.utils.reports import Report

    discord = Discord(webhook=WEBHOOK)

    # Create output with many lines
    lines = [f"Line {i}" for i in range(20)]
    long_output = "\n".join(lines)

    failed_db = DatabaseReport("test_db", False, long_output)

    report = Report()
    report.databases = [failed_db]
    discord.report = report

    optimized_output = discord._get_optimized_output()

    # Should only contain last 10 lines
    assert "Line 10" in optimized_output
    assert "Line 19" in optimized_output
    assert "Line 0" not in optimized_output
    assert "Line 5" not in optimized_output


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
