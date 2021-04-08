import requests

from blackbox.handlers.notifiers._base import BlackboxNotifier


class Discord(BlackboxNotifier):
    """A notifier for sending webhooks to Discord."""

    required_fields = ("webhook",)

    def _parse_report(self) -> dict:
        """Turn the report into something the notify function can use."""
        # Combine and truncate total output to < 2000 characters, fields don't support more.
        output = self.report.output[:2000]

        # Was this a success?
        success = self.report.success
        color = 1024049 if success else 13377568

        # Make a list of database fields
        fields = []
        for database in self.report.databases:
            field = {
                "name": f"**{database.database_id}**",
                "inline": True,
                "value": ""
            }

            for provider in database.storages:
                emoji = ":white_check_mark:" if provider.success else ":x:"
                field['value'] += f"{emoji}  {provider.storage_id}\n"

            # If all backup fails, no storage statuses will be added to
            # database['storage']. Discord doesn't allow empty field
            # values, so we have to add the :x: emoji to the field to
            # prevent the webhook endpoint from raising an error.
            if not field['value']:
                field['value'] = ":x:"

            # Strip any trailing newlines and append
            field['value'] = field['value'].strip()
            fields.append(field)

        # Add the output, but only if the overall report is a failure.
        if not success:
            fields.append({
                "name": "Output",
                "value": output,
            })

        # Return the payload
        return {
            "content": None,
            "embeds": [
                {
                    "title": "Backup",
                    "color": color,
                    "fields": fields
                }
            ],
            "username": "blackbox",
            "avatar_url": "https://raw.githubusercontent.com/lemonsaurus/blackbox/main/img/blackbox_avatar.png"
        }

    def notify(self):
        """Send a webhook to Discord with a blackbox report."""
        requests.post(self.config["webhook"], json=self._parse_report())
