from .databases.mongodb import MongoDB
from .databases.postgres import Postgres
from .databases.redis import Redis
from .notifiers.discord import Discord
from .storage.s3 import S3

all_databases = [
    MongoDB,
    Postgres,
    Redis,
]

all_storage_providers = [
    S3,
]

all_notifiers = [
    Discord,
]
