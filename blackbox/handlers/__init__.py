from .databases.mongodb import MongoDB
from .databases.postgres import Postgres
from .notifiers.discord import Discord
from .storage.s3 import S3

all_databases = [
    MongoDB,
    Postgres,
]

all_storage_providers = [
    S3,
]

all_notifiers = [
    Discord,
]
