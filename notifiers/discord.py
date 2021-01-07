import requests

from notifiers._base import BlackboxNotifier


class Discord(BlackboxNotifier):
    """A notifier for sending webhooks to Discord."""

    connstring_regex = r"discord://(?P<webhook_url>.+)"
    valid_uri_protocols = [
        "discord",
    ]

    def notify(self, report: dict) -> bool:
        """Send a webhook to Discord with a blackbox report."""
        requests.post(self.config.get("webhook_url"), {
            "content": str(report)
        })


