from .databases.mongodb import MongoDB
from .databases.postgres import Postgres
from .databases.redis import Redis
from .notifiers.discord import Discord
from .storage.google_drive import GoogleDrive

all_databases = [
    Redis,
    MongoDB,
    Postgres,
]

all_storage_providers = [
    GoogleDrive,
]

all_notifiers = [
    Discord,
]
