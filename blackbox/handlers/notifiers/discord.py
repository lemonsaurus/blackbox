import requests

from ._base import BlackboxNotifier


class Discord(BlackboxNotifier):
    """A notifier for sending webhooks to Discord."""

    connstring_regex = r"discord://(?P<webhook_url>.+)"
    valid_uri_protocols = [
        "discord",
    ]

    def _parse_report(self, report: dict) -> dict:
        """Turn the report from main.py into something the notify function can use."""

        # Combine and truncate total output to < 2000 characters, fields don't support more.
        output = report['output'][:2000]

        # Was this a success?
        success = report['success']
        color = 1024049 if success else 13377568

        # Make a list of database fields
        fields = []
        for database in report['databases'].values():
            field = {
                "name": f"**{database['type']}**",
                "inline": True,
                "value": ""
            }

            for provider in database['storage']:
                emoji = ":white_check_mark:" if provider['success'] else ":x:"
                field['value'] += f"{emoji}  {provider['type']}\n"

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
            "username":   "blackbox",
            "avatar_url": "https://raw.githubusercontent.com/lemonsaurus/blackbox/main/img/blackbox_avatar.png"
        }

    def notify(self, report: dict) -> bool:
        """Send a webhook to Discord with a blackbox report."""
        requests.post(self.config.get("webhook_url"), json=self._parse_report(report))
