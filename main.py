from databases import enabled_databases
from storage import enabled_storage_providers

if __name__ == "__main__":
    for db in enabled_databases:
        database = db()

        # Do a backup, and return the path to the backup file.
        backup_file = database.backup()

        # Sync the file to every provider
        for provider in enabled_storage_providers:
            provider.sync(backup_file)
