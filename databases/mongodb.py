from pathlib import Path

from config import BlackBox
from databases._base import BlackBoxDatabase
from utils import run_command


class MongoDB(BlackBoxDatabase):
    enabled = BlackBox.mongodb_enabled

    def backup(self) -> Path:
        raise NotImplementedError
