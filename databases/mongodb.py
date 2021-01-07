import logging
from pathlib import Path

from databases._base import BlackboxDatabase

log = logging.getLogger(__name__)


class MongoDB(BlackboxDatabase):
    """A Database handler that will do a mongodump for MongoDB, backing up all documents."""

    connstring_regex = r"mongo(?:db)?://(?P<user>.+):(?P<password>.+)@(?P<host>.+):(?P<port>.+)"
    valid_uri_protocols = [
        "mongo",
        "mongodb",
    ]

    def backup(self) -> Path:
        raise NotImplementedError
