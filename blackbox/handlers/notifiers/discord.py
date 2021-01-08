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
        raise NotImplementedError

    def notify(self, report: dict) -> bool:
        """Send a webhook to Discord with a blackbox report."""
        requests.post(self.config.get("webhook_url"), self._parse_report(report))


