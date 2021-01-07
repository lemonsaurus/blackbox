from pathlib import Path

from databases._base import BlackboxDatabase


class Redis(BlackboxDatabase):

    connstring_regex = r""
    valid_uri_protocols = []

    def backup(self) -> Path:
        raise NotImplementedError
