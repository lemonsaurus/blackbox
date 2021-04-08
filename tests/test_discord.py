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
        'avatar_url': 'https://raw.githubusercontent.com/lemonsaurus/blackbox/main/img/blackbox_avatar.png',
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
