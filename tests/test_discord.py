import requests_mock

from blackbox.handlers.notifiers.discord import Discord


def test_discord_notify(mocker, report):
    """Test report parsing for Discord notifications"""

    webhook_url = {
        "webhook_url": "https://discord.com/api/webhooks/x"
    }

    discord = Discord()
    Discord.config = webhook_url

    assert discord._parse_report(report) == {
        'avatar_url': 'https://raw.githubusercontent.com/lemonsaurus/blackbox/main/img/blackbox_avatar.png',
        'content': None,
        'embeds': [{'color': 1024049,
                    'fields': [{'inline': True,
                                'name': '**mongo**',
                                'value': ':white_check_mark:  s3'}],
                    'title': 'Backup'}],
        'username': 'blackbox'
    }

    with requests_mock.Mocker() as m:
        m.post(webhook_url["webhook_url"])
        discord.notify(report)
