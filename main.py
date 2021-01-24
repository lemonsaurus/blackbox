from blackbox.handlers.databases import BlackboxDatabase
from blackbox.handlers.storage import BlackboxStorage
from blackbox.handlers.notifiers import BlackboxNotifier

if __name__ == "__main__":
    report = {
        "output": "",
        "success": True,
        "databases": {},
    }

    for DatabaseHandler in BlackboxDatabase.__subclasses__():
        database = DatabaseHandler()
        database_type = DatabaseHandler.__name__

        if not database.enabled:
            continue

        # Do a backup, and return the path to the backup file.
        backup_file = database.backup()

        # Add the outcome to the report.
        report['databases'][database_type] = {
            "type": database_type,
            "storage": [],
        }

        # If one database failed, the overall report is a failure.
        report['output'] += database.output if not database.success else ""
        report['success'] = database.success if not database.success else report['success']

        # Do any cleanup needed.
        database.teardown()

        # Check the outcome of the backup.
        # If it failed, we'll add it to the report and continue
        # with the next database. No need to sync.
        if not database.success:
            continue

        # Otherwise, sync the backup file to every provider.
        for StorageProvider in BlackboxStorage.__subclasses__():
            storage_provider = StorageProvider()
            provider_type = StorageProvider.__name__

            if not storage_provider.enabled:
                continue

            # Sync the provider, and store the outcome to the report.
            storage_provider.sync(backup_file)
            report['databases'][database_type]['storage'].append({
                "type":    provider_type,
                "success": storage_provider.success,
            })
            report['output'] += storage_provider.output

            # If one storage handler failed, the overall report is a failure.
            report['success'] = storage_provider.success if not storage_provider.success else report['success']

            # Rotate, and then do cleanup
            storage_provider.rotate()
            storage_provider.teardown()

    # Now send a report to all notifiers.
    for Notifier in BlackboxNotifier.__subclasses__():
        notifier = Notifier()

        if not notifier.enabled:
            continue

        # Send a notification
        notifier.notify(report)

        # Do cleanup
        notifier.teardown()
