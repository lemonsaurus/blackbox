from abc import ABC, abstractmethod
from pathlib import Path


class BlackBoxDatabase(ABC):
    @abstractmethod
    def backup(self) -> Path:
        """
        Back up a database and return the Path for the backup file.

        All subclasses must implement this method.
        """
        raise NotImplementedError
