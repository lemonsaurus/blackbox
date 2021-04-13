import dataclasses

from blackbox.utils.mixins import SanitizeReportMixin


@dataclasses.dataclass
class StorageReport:
    """A report created by one of the Storage Handlers."""

    storage_id: str
    success: bool


@dataclasses.dataclass
class DatabaseReport(SanitizeReportMixin):
    """Keep database report."""

    database_id: str
    success: bool
    output: str
    storages: list[StorageReport] = dataclasses.field(default_factory=list)

    def report_storage(self, storage_id: str, success: bool, output: str):
        """Add a storage report to the current report."""
        # Add to database output
        self.output += self.sanitize_output(output)

        # If one storage handler failed, the database backup is a failure.
        if success is False:
            self.success = False

        # Add report to list of storages
        report = StorageReport(storage_id, success)
        self.storages.append(report)


@dataclasses.dataclass
class Report(SanitizeReportMixin):
    """Keep combined report."""

    databases: list[DatabaseReport] = dataclasses.field(default_factory=list)

    @property
    def success(self) -> bool:
        """Return whether or not the workflow is a success."""
        return all(report.success for report in self.databases)

    @property
    def output(self) -> str:
        """Return the combined outputs from all the database reports."""
        return self.sanitize_output("\n".join(report.output for report in self.databases))

    @property
    def is_empty(self) -> bool:
        """Return whether or not there are no databases in the report."""
        return self.databases == []
