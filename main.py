from blackbox.handlers import all_databases, all_storage_providers, all_notifiers

if __name__ == "__main__":
    report = {}
    for DatabaseHandler in all_databases:
        database = DatabaseHandler()

        if not database.enabled:
            continue

        # Do a backup, and return the path to the backup file.
        backup_file = database.backup()

        # Add the outcome to the report.
        report[DatabaseHandler.__name__] = {
            "state":  "success" if database.success else "failed",
            "output": database.output,
        }

        # Check the outcome of the backup.
        # If it failed, we'll add it to the report and continue
        # with the next database. No need to sync.
        if not database.success:
            continue

        # Otherwise, sync the backup file to every provider.
        for StorageProvider in all_storage_providers:
            provider = StorageProvider()

            if not provider.enabled:
                continue

            provider.sync(backup_file)

    print(report)
