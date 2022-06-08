from pathlib import Path
from zipfile import ZIP_DEFLATED
from zipfile import ZipFile

from blackbox.exceptions import ImproperlyConfigured
from blackbox.handlers.databases._base import BlackboxDatabase


class LocalStorage(BlackboxDatabase):
    """A Database handler that will zip a local folder."""

    required_fields = ("path",)

    def __init__(self, **kwargs) -> None:
        # Gzip deflates only accept compression level ranging from 0 to 9
        # if the argument is given, we check it is in the allowed range otherwise
        # RuntimeError will be raised by ZipFile
        if compression_level := kwargs.get("compression_level"):
            if compression_level < 0 or compression_level > 9:
                raise ImproperlyConfigured(
                    f"Invalid compression level. "
                    f"Must be an integer between 0 and 9, got {compression_level}."
                )

        super().__init__(**kwargs)

    def backup(self, backup_path: Path) -> None:
        path = self.config["path"]
        compression_level = self.config.get("compression_level", 5)

        # Store evey file in the archive
        # We use deflate (Gzip) for compression and the level has already been validated in __init__
        with ZipFile(backup_path, "w", ZIP_DEFLATED, compresslevel=compression_level) as zipfile:
            for subpath in Path(path).rglob("*"):
                if subpath.is_file():
                    zipfile.write(subpath)

        # The compression was successful
        self.success = True
