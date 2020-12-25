from databases import Redis, Postgres, MongoDB
from storage import GoogleDrive

databases = [Redis, Postgres, MongoDB]
storage_providers = [GoogleDrive]

if __name__ == "__main__":
    for db in databases:
        database = db()

        # Do a backup, and return the path to the backup file.
        backup_file = database.backup()

        # Sync the file to every provider
        for provider in storage_providers:
            provider.sync(backup_file)
