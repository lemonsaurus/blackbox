from abc import abstractmethod

from blackbox.handlers._base import BlackboxHandler
from blackbox.utils import reports


class BlackboxNotifier(BlackboxHandler):
    """An abstract interface for creating Blackbox Notifiers."""

    handler_type = "notifier"
    # Default character limit - subclasses can override
    max_output_chars = 2000

    def __init__(self, **kwargs):
        """Set up notifier handler."""
        super().__init__(**kwargs)
        self.report = reports.Report()

    def get_optimized_output(self) -> str:
        """
        Generate optimally truncated output for failed databases only.

        Only includes output from databases that failed, using tail of logs
        and optimal character allocation to maximize relevant information.
        """
        # Get failed databases only
        failed_databases = [db for db in self.report.databases if not db.success]

        if not failed_databases:
            return ""

        # Get tail of each failed database output (last 10 lines max)
        database_outputs = []
        for db in failed_databases:
            lines = db.output.strip().split('\n')
            tail_lines = lines[-10:] if len(lines) > 10 else lines
            tail_output = '\n'.join(tail_lines)
            database_outputs.append((db.database_id, tail_output))

        # If only one failed database, just truncate to character limit
        if len(database_outputs) == 1:
            db_id, output = database_outputs[0]
            if len(output) <= self.max_output_chars:
                return output
            return output[-self.max_output_chars:]  # Take last N characters

        # Multiple failed databases - use optimal allocation algorithm
        return self._allocate_characters_optimally(database_outputs)

    def _allocate_characters_optimally(self, database_outputs: list[tuple[str, str]]) -> str:
        """
        Implement optimal character allocation algorithm from issue #155.

        Sorts outputs by length and allocates characters to minimize truncation
        while staying within the character limit.
        """
        # Sort by output length (smallest first)
        sorted_outputs = sorted(database_outputs, key=lambda x: len(x[1]))

        total_budget = self.max_output_chars
        allocated_outputs = []
        remaining_services = len(sorted_outputs)

        for db_id, output in sorted_outputs:
            # Calculate budget for this service
            if remaining_services == 0 or total_budget <= 0:
                break
            budget_per_service = total_budget // remaining_services

            # Calculate the formatted output length including separators
            separator_overhead = len("\n\n") if allocated_outputs else 0
            db_prefix = f"{db_id}: "

            if len(output) + len(db_prefix) + separator_overhead <= budget_per_service:
                # Output fits within budget, use as-is
                formatted = f"{db_id}: {output}"
                allocated_outputs.append(formatted)
                total_budget -= (len(formatted) + separator_overhead)
            else:
                # Output exceeds budget, truncate from start (keep tail)
                available_chars = budget_per_service - len(db_prefix) - separator_overhead
                if available_chars > 0:
                    truncated = output[-available_chars:]
                    formatted = f"{db_id}: {truncated}"
                    allocated_outputs.append(formatted)
                    total_budget -= budget_per_service
                else:
                    # Not enough space even for the database ID
                    break

            remaining_services -= 1

        return "\n\n".join(allocated_outputs)

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
