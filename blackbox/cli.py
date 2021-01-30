from pathlib import Path
from textwrap import dedent

import click

from blackbox.__version__ import __version__
from blackbox.config import YAMLGetter
from blackbox.handlers.databases import BlackboxDatabase
from blackbox.handlers.notifiers import BlackboxNotifier
from blackbox.handlers.storage import BlackboxStorage


@click.command()
@click.option('--config', default="blackbox.yml", help="Path to blackbox.yaml file")
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
                "type": provider_type,
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

    # If this failed, we'll exit with a non-zero exit code, to indicate
    # a failure. Might be useful for Kubernetes jobs.
    if not report.get("success"):
        exit(1)
