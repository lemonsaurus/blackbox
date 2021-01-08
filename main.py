from blackbox.handlers import all_databases, all_storage_providers, all_notifiers

if __name__ == "__main__":
    report = {
        "output": "",
        "success": True,
        "databases": {},
    }
    for DatabaseHandler in all_databases:
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

        # Check the outcome of the backup.
        # If it failed, we'll add it to the report and continue
        # with the next database. No need to sync.
        if not database.success:
            continue

        # Otherwise, sync the backup file to every provider.
        for StorageProvider in all_storage_providers:
            provider = StorageProvider()
            provider_type = StorageProvider.__name__

            if not provider.enabled:
                continue

            # Sync the provider, and store the outcome to the report.
            provider.sync(backup_file)
            report['databases'][database_type]['storage'].append({
                "type": provider_type,
                "success": provider.success,
            })
            report['output'] += provider.output

            # If one storage handler failed, the overall report is a failure.
            report['success'] = provider.success if not provider.success else report['success']

    # Now send a report to all notifiers.
    for Notifier in all_notifiers:
        notifier = Notifier()

        if not notifier.enabled:
            continue

        # Send a notification
        notifier.notify(report)
