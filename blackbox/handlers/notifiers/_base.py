from abc import ABC, abstractmethod

from blackbox.mixins import ConnstringParserMixin


class BlackboxNotifier(ABC, ConnstringParserMixin):
    @abstractmethod
    def _parse_report(self, report: dict) -> dict:
        """Turn the report from main.py into something the notify function can use."""
        raise NotImplementedError

    @abstractmethod
    def notify(self, report: dict) -> bool:
        """Send a notification to the configured notifier."""
        raise NotImplementedError
