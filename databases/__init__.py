from .redis import Redis
from .mongodb import MongoDB
from .postgres import Postgres

databases = [
    Redis,
    MongoDB,
    Postgres,
]
enabled_databases = [db for db in databases if db.enabled]

