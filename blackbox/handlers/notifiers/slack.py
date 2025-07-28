import requests

from blackbox.handlers.notifiers._base import BlackboxNotifier


class Slack(BlackboxNotifier):
    """A notifier for sending webhooks to Slack."""

    required_fields = ("webhook",)
    # Slack field character limit is 2000 for attachment fields
    max_output_chars = 2000

    def _parse_report(self) -> dict:
        """Turn the report from main.py into something the notify function can use."""
        if self.config.get("use_block_kit"):
            return self._parse_report_modern()

        return self._parse_report_classic()

    def _parse_report_classic(self) -> dict:
        """Turn the report from main.py into Slack webhook payload with secondary attachment."""
        attachment = {
            "mrkdwn_in": ["fields"],
            "title": "Backup",
            "author_name": "blackbox",
            "author_icon": "https://raw.githubusercontent.com/lemonsaurus/blackbox/main/img/blackbox_avatar.png"  # NOQA: E501
        }

        # Generate optimally truncated output for failed databases only
        output = self.get_optimized_output()

        # Was this a success?
        success = self.report.success
        attachment["color"] = "#0FA031" if success else "#CC2020"

        # Make a list of database fields
        fields = []
        for database in self.report.databases:
            field = {
                "title": f"{database.database_id}",
                "short": True,
                "value": ""
            }

            for provider in database.storages:
                emoji = ":white_check_mark:" if provider.success else ":x:"
                field['value'] += f"{emoji}  {provider.storage_id}\n"

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

    def _parse_report_modern(self) -> dict:
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
        success = self.report.success
        databases = list(self.report.databases)

        for i in range(0, len(databases), 2):
            dbs = [databases[i]]
            if len(databases) > i + 1:
                dbs.append(databases[i + 1])

            fields = []
            for db in dbs:
                field = {
                    "type": "mrkdwn",
                    "text": f"*{db.database_id}*"
                }

                for provider in db.storages:
                    emoji = ":white_check_mark:" if provider.success else ":x:"
                    field["text"] += f"\n{emoji} {provider.storage_id}"

                # Indicate that backup have failed if no storage providers was used.
                if field["text"] == f"*{db.database_id}*":
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
            # Generate optimally truncated output for failed databases only
            output = self.get_optimized_output()
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
                        "image_url": "https://raw.githubusercontent.com/lemonsaurus/blackbox/main/img/blackbox_avatar.png",  # NOQA: E501
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

    def notify(self) -> None:
        """Send a webhook to Slack with a blackbox report."""
        requests.post(self.config["webhook"], json=self._parse_report())
