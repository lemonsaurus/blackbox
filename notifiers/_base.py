from abc import ABC, abstractmethod

from blackbox.mixins import ConnstringParserMixin


class BlackboxNotifier(ABC, ConnstringParserMixin):
    @abstractmethod
    def notify(self, report: dict) -> bool:
        """Send a notification to the configured notifier."""
        raise NotImplementedError
