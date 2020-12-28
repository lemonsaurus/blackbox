from pathlib import Path

from databases._base import BlackBoxDatabase


class Redis(BlackBoxDatabase):
    enabled = False

    def backup(self) -> Path:
        raise NotImplementedError
