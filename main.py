import itertools

from blackbox.config import Blackbox as CONFIG
from blackbox.handlers.databases import BlackboxDatabase
from blackbox.handlers.notifiers import BlackboxNotifier
from blackbox.handlers.storage import BlackboxStorage
from blackbox.utils.logger import log
from blackbox.workflows import get_configured_handlers
from blackbox.workflows import get_workflows


def main():
    """Main function of Blackbox."""

    # Parse configuration and instantiate handlers
    configured_storage_providers = get_configured_handlers(BlackboxStorage, CONFIG.storage)
    configured_notifiers = get_configured_handlers(BlackboxNotifier, CONFIG.notifiers)
    configured_databases = get_configured_handlers(BlackboxDatabase, CONFIG.databases)

    workflows = get_workflows(
        configured_databases, configured_storage_providers, configured_notifiers
    )

    # Counter to ensure handlers have unique ids
    # This does not get used if the handler specifies an id
    id_counter = itertools.count()

    # Go through each workflow
    for workflow in workflows:
        database = workflow.database
        log.debug(f"Backing up: {database}")

        # Workflow report
        database_id = (
            f"{database.__class__.__name__}-{database.config.get('id', next(id_counter))}"
        )
        report = {
            "output": "",
            "success": True,
            "id": database_id,
            "storage": []
        }

        # Do a backup, and return the path to the backup file.
        backup_file = database.backup()

        log.debug(f"Database success: {database.success}")
        # Add the outcome to the report
        if database.success is False:
            report["output"] += database.output
            report["success"] = False

        # Do any cleanup needed
        database.teardown()

        # Check the outcome of the backup.
        # If it failed, we'll add it to the report and continue
        # with the next database. No need to sync.
        if not database.success:
            continue

        # Otherwise, sync the backup file to every provider.
        for storage_provider in workflow.storage_providers:
            log.debug(f"Syncing {database} to {storage_provider}")
            storage_id = (
                f"{storage_provider.__class__.__name__}"
                f"-{storage_provider.config.get('id', next(id_counter))}"
            )

            # Sync the provider, and store the outcome to the report.
            storage_provider.sync(backup_file)
            report["storage"].append({
                "id": storage_id,
                "success": storage_provider.success,
            })
            report["output"] += storage_provider.output

            log.debug(f"Storage provider success: {storage_provider.success}")
            # If one storage handler failed, the overall report is a failure.
            if not storage_provider.success:
                report["success"] = False

            # Rotate, and then do cleanup
            storage_provider.rotate()
            storage_provider.teardown()

        # Now add the report to specified notifiers
        for notifier in workflow.notifiers:
            log.debug(f"Adding {database} report to {notifier}")
            notifier.add_report(report)

    # Send a report for each notifier configured
    for notifier in configured_notifiers["all"]:
        log.debug(f"Sending notifier: {notifier}")
        notifier.notify()
        notifier.teardown()


if __name__ == "__main__":
    main()
