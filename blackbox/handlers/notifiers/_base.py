from abc import abstractmethod

from blackbox.handlers._base import BlackboxHandler


class BlackboxNotifier(BlackboxHandler):
    @abstractmethod
    def _parse_report(self, report: dict) -> dict:
        """Turn the report from main.py into something the notify function can use."""
        raise NotImplementedError

    @abstractmethod
    def notify(self, report: dict) -> bool:
        """Send a notification to the configured notifier."""
        raise NotImplementedError
