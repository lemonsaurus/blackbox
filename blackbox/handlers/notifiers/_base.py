import dataclasses
from abc import abstractmethod

from blackbox.handlers._base import BlackboxHandler
from blackbox.utils.reports import DatabaseReport


@dataclasses.dataclass
class Report:
    databases: list[DatabaseReport] = dataclasses.field(default_factory=list)

    @property
    def success(self) -> bool:
        """Return whether or not the workflow is a success."""
        return all(report.success for report in self.databases)

    @property
    def output(self) -> str:
        """Return the combined outputs from all the database reports."""
        return "\n".join(report.output for report in self.databases)


class BlackboxNotifier(BlackboxHandler):
    """An abstract interface for creating Blackbox Notifiers."""

    handler_type = "notifier"

    def __init__(self, **kwargs):
        """Set up notiifer handler."""
        super().__init__(**kwargs)
        self.report = Report()

    @abstractmethod
    def _parse_report(self) -> dict:
        """Turn the report into something the notify function can use."""
        raise NotImplementedError

    @abstractmethod
    def notify(self):
        """Send a notification to the configured notifier."""
        raise NotImplementedError

    def add_database(self, report: DatabaseReport):
        """Add a database report to the current list of reports."""
        self.report.databases.append(report)
