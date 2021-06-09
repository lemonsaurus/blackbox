import datetime
from collections import deque
from pathlib import Path
from zipfile import ZIP_DEFLATED
from zipfile import ZipFile

from blackbox.exceptions import ImproperlyConfigured
from blackbox.handlers.databases._base import BlackboxDatabase


class LocalStorage(BlackboxDatabase):
    """A Database handler that will zip a local folder."""

    required_fields = ("path",)

    def backup(self) -> Path:
        date = datetime.date.today().strftime("%d_%m_%Y")

        path = self.config["path"]
        compression_level = self.config.get("compression_level", 5)

        if compression_level < 0 or compression_level > 9:
            raise ImproperlyConfigured(
                f"Invalid compression level. Must be an integer between 0 and 9, got {compression_level}."
            )

        backup_path = Path.home() / f"{self.config['id']}_blackbox_{date}.zip"

        with ZipFile(backup_path, "w", ZIP_DEFLATED, compresslevel=compression_level) as zipfile:
            directories = deque((Path(path),))

            while not len(directories) == 0:
                path = directories.pop()

                for file in path.iterdir():
                    if file.is_file():
                        zipfile.write(file)
                    elif file.is_dir():
                        directories.append(file)

        self.success = True
        return backup_path
