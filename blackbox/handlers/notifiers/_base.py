from abc import abstractmethod

from blackbox.handlers._base import BlackboxHandler


class BlackboxNotifier(BlackboxHandler):
    """An abstract interface for creating Blackbox Notifiers."""

    handler_type = "notifier"

    def __init__(self, **kwargs):
        """Set up notiifer handler."""
        super().__init__(**kwargs)

    @abstractmethod
    def _parse_report(self, report: dict) -> dict:
        """Turn the report from main.py into something the notify function can use."""
        raise NotImplementedError

    @abstractmethod
    def notify(self, report: dict) -> bool:
        """Send a notification to the configured notifier."""
        raise NotImplementedError
