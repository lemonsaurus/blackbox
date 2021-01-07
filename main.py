from databases import all_databases
from storage import all_storage_providers

if __name__ == "__main__":
    for DatabaseHandler in all_databases:
        database = DatabaseHandler()

        if not database.enabled:
            continue

        # Do a backup, and return the path to the backup file.
        backup_file = database.backup()

        # Sync the file to every provider
        for StorageProvider in all_storage_providers:
            provider = StorageProvider()

            if not provider.enabled:
                continue

            provider.sync(backup_file)
