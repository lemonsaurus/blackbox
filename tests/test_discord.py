import requests_mock

from blackbox.handlers.notifiers.discord import Discord


def test_discord_notify(mocker):
    """Test report parsing for Discord notifications"""

    webhook_url = {
        "webhook_url": "https://discord.com/api/webhooks/x"
    }

    report = {
        "output": "salad",
        "success": "maybe",
        "databases": {
            "s3": {"type": "databasetype", "storage": []},
        }
    }

    discord = Discord()
    Discord.config = webhook_url

    assert discord._parse_report(report) == {
        'avatar_url': 'https://raw.githubusercontent.com/lemonsaurus/blackbox/main/img/blackbox_avatar.png',
        'content': None,
        'embeds': [{'color': 1024049,
                    'fields': [{'inline': True,
                                'name': '**databasetype**',
                                'value': ':x:'}],
                    'title': 'Backup'}],
        'username': 'blackbox'
    }

    with requests_mock.Mocker() as m:
        m.post(requests_mock.ANY, json=report)
        discord.notify(report)

        {'avatar_url': 'https://raw.githubusercontent.com/lemonsaurus/blackbox/main/img/blackbox_avatar.png',
         'content': None,
         'embeds': [{'color': 1024049,
                     'fields': [{'inline': True,
                                 'name': '**databasetype**',
                                 'value': ':x:'}],
                     'title': 'Backup'}],
         'username': 'blackbox'}
