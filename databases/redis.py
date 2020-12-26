from pathlib import Path

from config import BlackBox
from databases._base import BlackBoxDatabase
from utils import run_command


class Redis(BlackBoxDatabase):
    enabled = BlackBox.redis_enabled

    def backup(self) -> Path:
        raise NotImplementedError


if __name__ == "__main__":
    redis = Redis()
