from pathlib import Path
from textwrap import dedent

import click

from blackbox import exceptions
from blackbox.__version__ import __version__
from blackbox.config import Blackbox as CONFIG
from blackbox.config import YAMLGetter
from blackbox.utils import workflows
from blackbox.utils.reports import DatabaseReport


def run() -> bool:
    """
    The main blackbox process.

    Returns whether or not the process is a success.
    """
    # Overall program success
    success = True

    # Parse configuration and instantiate handlers
    if not CONFIG.databases or not CONFIG.storage:
        raise exceptions.ImproperlyConfigured("You have to define least one database and storage")

    database_handlers = workflows.get_configured_handlers(CONFIG.databases)
    storage_handlers = workflows.get_configured_handlers(CONFIG.storage)
    notifier_handlers = workflows.get_configured_handlers(CONFIG.notifiers)

    all_workflows = workflows.get_workflows(database_handlers, storage_handlers, notifier_handlers)

    for workflow in all_workflows:
        database = workflow.database

        # Do a backup, then return the path to the backup file
        backup_file = database.backup()
        database.teardown()

        # Add report to notifiers
        report = DatabaseReport(database.config["id"], database.success, database.output)
        for notifier in workflow.notifiers:
            notifier.add_database(report)

        # If backup failed, continue to next database. No need to sync.
        if not database.success:
            continue

        for storage in workflow.storage_providers:
            # Sync the provider, then rotate and cleanup
            storage.sync(backup_file)
            storage.rotate()
            storage.teardown()

            # Store the outcome to the database report
            report.report_storage(storage.config["id"], storage.success, storage.output)

        # Set overall program success to False if workflow is unsuccessful
        if report.success is False:
            success = False

    # Send a report for each notifier configured
    for notifier in notifier_handlers["all"]:
        notifier.notify()
        notifier.teardown()

    return success


@click.command()
@click.option('--config', help="Path to blackbox.yaml file")
@click.option('--init', is_flag=True, help="Generate blackbox.yaml file and exit")
@click.option('--version', is_flag=True, help="Show version and exit")
def cli(config, init, version):
    """
    BLACKBOX

    Backup database to external storage system
    """

    if version:
        print(__version__, flush=True)
        exit()

    if init:
        config_file = Path("blackbox.yaml")
        if not config_file.exists():
            config_file.write_text(dedent(
                """
                databases:
                  - mongodb://username:password@host:port
                  - postgres://username:password@host:port
                  - redis://password@host:port

                storage:
                  - s3://bucket:s3.endpoint.com?aws_access_key_id=1234&aws_secret_access_key=lemondance

                notifiers:
                  - https://web.hook/

                retention_days: 7
                """).lstrip()
            )
            print("blackbox.yaml configuration created", flush=True)

        else:
            print("blackbox.yaml already exists", flush=True)

        exit()

    if config:
        YAMLGetter.parse_config(Path(config))

    success = run()
    # If this failed, we'll exit with a non-zero exit code, to indicate
    # a failure. Might be useful for Kubernetes jobs.
    if not success:
        exit(1)
