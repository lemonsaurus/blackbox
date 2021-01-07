from .redis import Redis
from .mongodb import MongoDB
from .postgres import Postgres

all_databases = [
    Redis,
    MongoDB,
    Postgres,
]

