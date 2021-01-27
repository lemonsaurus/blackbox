from abc import abstractmethod

from blackbox.handlers._base import BlackboxHandler


class BlackboxNotifier(BlackboxHandler):
    """An abstract notifier handler."""

    def __init__(self, *args, **kwargs):
        """"Set up notifier handler."""
        super().__init__(*args, **kwargs)
        self.report = {
            "output": "",
            "success": True,
            "databases": {},
        }

    def add_report(self, report: dict):
        """Adds the report to the current report."""
        # Append output to current report output
        self.report["output"] += report.pop("output")

        # If a report is a failure, the overall report is a failure
        if report.pop("success") is False:
            self.report["success"] = False

        # Add the database contained in the report
        self.report["databases"][report["type"]] = report

    @abstractmethod
    def _parse_report(self, report: dict) -> dict:
        """Turn the report from main.py into something the notify function can use."""
        raise NotImplementedError

    @abstractmethod
    def notify(self) -> bool:
        """Send a notification to the configured notifier."""
        raise NotImplementedError
