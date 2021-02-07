import requests_mock

from blackbox.handlers.notifiers.slack import Slack


def test_slack_notify(mocker, report):
    """Test report parsing for Discord notifications"""

    webhook_url = {
        "webhook_url": "https://hooks.slack.com/services/x/x/x"
    }

    slack = Slack()
    Slack.config = webhook_url

    assert slack._parse_report(report) == {
        'attachments': [
            {
                'author_icon': 'https://raw.githubusercontent.com/lemonsaurus/blackbox/main/img/blackbox_avatar.png',
                'author_name': 'blackbox',
                'color': '#0FA031',

                'fields': [{'short': True,
                            'title': 'mongo',
                            'value': ':white_check_mark:  s3'}],
                'mrkdwn_in': ['fields'],
                'title': 'Backup'
            }
        ]
    }

    with requests_mock.Mocker() as m:
        m.post(webhook_url["webhook_url"])
        slack.notify(report)


def test_slack_notify_modern(mocker, report):
    """Test report parsing for Discord notifications"""

    webhook_url = {
        "webhook_url": "https://hooks.slack.com/services/x/x/x",
        "use_block_kit": True
    }

    slack = Slack()
    Slack.config = webhook_url

    assert slack._parse_report(report) == {
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
                        'text': '*mongo*\n:white_check_mark: s3', 'type': 'mrkdwn'
                    }
                ], 'type': 'section'
            },
            {
                'elements': [
                    {
                        'alt_text': 'blackbox',
                        'image_url': 'https://raw.githubusercontent.com/lemonsaurus/blackbox/main/img/blackbox_avatar.png',
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
        m.post(webhook_url["webhook_url"])
        slack.notify(report)
