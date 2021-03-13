import requests

from blackbox.handlers.notifiers._base import BlackboxNotifier


class Slack(BlackboxNotifier):
    """A notifier for sending webhooks to Slack."""

    required_fields = ("webhook",)

    def _parse_report(self, report: dict) -> dict:
        """Turn the report from main.py into something the notify function can use."""
        if self.config.get("use_block_kit"):
            return self._parse_report_modern(report)

        return self._parse_report_classic(report)

    def _parse_report_classic(self, report: dict) -> dict:
        """Turn the report from main.py into Slack webhook payload with secondary attachment."""
        attachment = {
            "mrkdwn_in": ["fields"],
            "title": "Backup",
            "author_name": "blackbox",
            "author_icon": "https://raw.githubusercontent.com/lemonsaurus/blackbox/main/img/blackbox_avatar.png"
        }

        # Combine and truncate total output to < 2000 characters, fields don't support more.
        output = report['output'][:2000]

        # Was this a success?
        success = report['success']
        attachment["color"] = "#0FA031" if success else "#CC2020"

        # Make a list of database fields
        fields = []
        for database in report['databases'].values():
            field = {
                "title": f"{database['type']}",
                "short": True,
                "value": ""
            }

            for provider in database['storage']:
                emoji = ":white_check_mark:" if provider['success'] else ":x:"
                field['value'] += f"{emoji}  {provider['type']}\n"

            # Indicate that backup have failed if no storage providers was used.
            if not field['value']:
                field['value'] = ":x:"

            # Strip any trailing newlines and append
            field['value'] = field['value'].strip()
            fields.append(field)

        if not success:
            fields.append({
                "title": "Output",
                "value": output
            })

        attachment["fields"] = fields

        return {
            "attachments": [attachment]
        }

    def _parse_report_modern(self, report: dict) -> dict:
        """Turn the report from main.py into Slack webhook payload with Block Kit."""
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "Backup"
                }
            }
        ]

        # Was this a success?
        success = report['success']
        databases = list(report['databases'].values())

        for i in range(0, len(databases), 2):
            dbs = [databases[i]]
            if len(databases) > i + 1:
                dbs.append(databases[i + 1])

            fields = []
            for db in dbs:
                field = {
                    "type": "mrkdwn",
                    "text": f"*{db['type']}*"
                }

                for provider in db['storage']:
                    emoji = ":white_check_mark:" if provider['success'] else ":x:"
                    field["text"] += f"\n{emoji} {provider['type']}"

                # Indicate that backup have failed if no storage providers was used.
                if field["text"] == f"*{db['type']}*":
                    field["text"] += "\n:x:"

                # Strip any trailing newlines and append
                field['text'] = field['text'].strip()
                fields.append(field)

            section = {
                "type": "section",
                "fields": fields
            }
            blocks.append(section)

        if not success:
            # Combine and truncate total output to < 2000 characters, fields don't support more.
            output = report['output'][:2000]
            blocks += [
                {
                    "type": "divider"
                },
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "Output"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "plain_text",
                        "text": output
                    }
                }
            ]

        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "image",
                        "image_url": "https://raw.githubusercontent.com/lemonsaurus/blackbox/main/img/blackbox_avatar.png",
                        "alt_text": "blackbox"
                    },
                    {
                        "type": "plain_text",
                        "text": "blackbox",
                        "emoji": True
                    }
                ]
            }
        )

        return {"blocks": blocks}

    def notify(self, report: dict) -> None:
        """Send a webhook to Slack with a blackbox report."""
        requests.post(self.config["webhook"], json=self._parse_report(report))
