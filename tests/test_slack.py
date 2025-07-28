import pytest
import requests_mock

from blackbox.exceptions import MissingFields
from blackbox.handlers.notifiers.slack import Slack


WEBHOOK = "https://hooks.slack.com/services/x/x/x"


@pytest.fixture
def mock_valid_slack_config():
    """Mock valid Slack config."""
    return {"webhook": WEBHOOK}


@pytest.fixture
def mock_valid_slack_config_with_block_kit():
    """Mock valid Slack config with block kit usage."""
    return {"webhook": WEBHOOK, "use_block_kit": True}


@pytest.fixture
def mock_invalid_slack_config():
    """Mock invalid Slack config."""
    return {}


def test_slack_handler_can_be_instantiated_with_required_fields(mock_valid_slack_config):
    """Test if the slack notifier handler can be instantiated."""
    Slack(**mock_valid_slack_config)


def test_slack_handler_fails_without_required_fields(mock_invalid_slack_config):
    """Test if the slack notifier handler cannot be instantiated with missing fields."""
    with pytest.raises(MissingFields):
        Slack(**mock_invalid_slack_config)


def test_slack_handler_instantiates_optional_fields(mock_valid_slack_config_with_block_kit):
    """Test if the slack notifier handler instantiates optional fields."""
    slack_instance = Slack(**mock_valid_slack_config_with_block_kit)
    assert slack_instance.config["use_block_kit"] is True


def test_slack_notify(mock_valid_slack_config, report):
    """Test report parsing for slack notifications."""
    slack = Slack(**mock_valid_slack_config)
    slack.report = report

    assert slack._parse_report() == {
        'attachments': [
            {
                'author_icon': 'https://raw.githubusercontent.com/lemonsaurus/blackbox/main/img/blackbox_avatar.png',  # NOQA: E501
                'author_name': 'blackbox',
                'color': '#0FA031',

                'fields': [{'short': True,
                            'title': 'main_mongo',
                            'value': ':white_check_mark:  main_s3'}],
                'mrkdwn_in': ['fields'],
                'title': 'Backup'
            }
        ]
    }

    with requests_mock.Mocker() as m:
        m.post(WEBHOOK)
        slack.notify()


def test_slack_uses_2000_character_limit():
    """Test that Slack specifically uses 2000 character limit."""
    from blackbox.utils.reports import DatabaseReport
    from blackbox.utils.reports import Report

    slack = Slack(webhook=WEBHOOK)

    # Verify Slack's character limit is set correctly
    assert slack.max_output_chars == 2000

    # Create a failed database with output longer than 2000 chars
    long_output = "Error: " + "x" * 3000
    failed_db = DatabaseReport("failed_db", False, long_output)

    report = Report()
    report.databases = [failed_db]
    slack.report = report

    optimized_output = slack.get_optimized_output()

    # Should be truncated to Slack's 2000 character limit
    assert len(optimized_output) <= 2000


def test_slack_notify_modern(mock_valid_slack_config_with_block_kit, report):
    """Test report parsing for slack notifications."""
    slack = Slack(**mock_valid_slack_config_with_block_kit)
    slack.report = report

    assert slack._parse_report() == {
        'blocks': [
            {
                'text': {
                    'text': 'Backup', 'type': 'plain_text'
                },
                'type': 'header'
            },
            {
                'fields': [
                    {
                        'text': '*main_mongo*\n:white_check_mark: main_s3', 'type': 'mrkdwn'
                    }
                ], 'type': 'section'
            },
            {
                'elements': [
                    {
                        'alt_text': 'blackbox',
                        'image_url': 'https://raw.githubusercontent.com/lemonsaurus/blackbox/main/img/blackbox_avatar.png',  # NOQA: E501
                        'type': 'image'
                    },
                    {
                        'emoji': True,
                        'text': 'blackbox',
                        'type': 'plain_text'
                    }
                ],
                'type': 'context'
            }
        ]
    }

    with requests_mock.Mocker() as m:
        m.post(WEBHOOK)
