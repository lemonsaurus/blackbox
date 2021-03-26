from abc import abstractmethod

from blackbox.handlers._base import BlackboxHandler
from blackbox.utils import reports


class BlackboxNotifier(BlackboxHandler):
    """An abstract interface for creating Blackbox Notifiers."""

    handler_type = "notifier"

    def __init__(self, **kwargs):
        """Set up notifier handler."""
        super().__init__(**kwargs)
        self.report = reports.Report()

    @abstractmethod
    def _parse_report(self) -> dict:
        """Turn the report into something the notify function can use."""
        raise NotImplementedError

    @abstractmethod
    def notify(self):
        """Send a notification to the configured notifier."""
        raise NotImplementedError

    def add_database(self, report: reports.DatabaseReport):
        """Add a database report to the current list of reports."""
        self.report.databases.append(report)
