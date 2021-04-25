from blackbox.handlers.databases import MariaDB
from blackbox.handlers.databases._base import BlackboxDatabase


class MySQL(MariaDB, BlackboxDatabase):
    """A Database handler that will do a mysqldump for MySQL, backing up all tables."""

    pass
