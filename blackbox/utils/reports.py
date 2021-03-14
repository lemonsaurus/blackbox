import dataclasses


@dataclasses.dataclass
class StorageReport:
    storage_id: str
    success: bool


@dataclasses.dataclass
class DatabaseReport:
    database_id: str
    success: bool
    output: str
    storages: list[StorageReport] = dataclasses.field(default_factory=list)

    def report_storage(self, storage_id: str, success: bool, output: str):
        """Add a storage report to the current report."""
        # Add to database output
        self.output += output

        # If one storage handler failed, the database backup is a failure.
        if success is False:
            self.success = False

        # Add report to list of storages
        report = StorageReport(storage_id, success)
        self.storages.append(report)
