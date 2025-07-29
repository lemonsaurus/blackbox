import gzip
import shutil
import tempfile
import typing
from abc import abstractmethod
from datetime import datetime
from functools import partial
from pathlib import Path

import blackbox.utils.rotation as rotation
from blackbox.config import Blackbox
from blackbox.handlers._base import BlackboxHandler
from blackbox.utils.encryption import create_encryption_handler
from blackbox.utils.logger import log


# File suffixes considered as archives
ARCHIVE_SUFFIXES = {".tar", ".zip"}


class BlackboxStorage(BlackboxHandler):
    """An abstract interface for creating Blackbox Storage Providers."""

    handler_type = "storage"

    def __init__(self, **kwargs):
        """Initialize storage handler with encryption and rotation config."""
        super().__init__(**kwargs)

        self.success = False  # Upload success status
        self.output = ""     # Storage operation output/errors

        # Track backup retention counts per rotation strategy
        self.rotation_strategies = self.config.get("rotation_strategies", [])
        self.backups_retained = rotation.construct_retention_tracker(
            cron_expressions=self.rotation_strategies,
        )

        # Initialize encryption handler from config
        encryption_config = self.config.get("encryption", Blackbox.encryption or {})
        self.encryption_handler = create_encryption_handler({"encryption": encryption_config})

    @staticmethod
    def compress(file_path: Path) -> tuple[typing.IO, bool]:
        """Compress file with gzip unless archive. Returns (file_obj, was_compressed)."""
        # Skip compression for archives (.tar, .zip)
        if file_path.suffix in ARCHIVE_SUFFIXES:
            log.debug(f"File {file_path.name} is already compressed.")
            return open(file_path, "rb"), False

        temp_file = tempfile.NamedTemporaryFile(suffix=f"-{file_path.name}")

        log.debug(f"Compressing to temporary file: {temp_file.name}")
        with file_path.open(mode="rb") as f_in:
            with gzip.open(temp_file, "wb") as f_out:
                shutil.copyfileobj(f_in, f_out)

        temp_file.seek(0)
        return temp_file, True

    def encrypt_file(self, file_path: Path) -> tuple[Path, bool]:
        """Encrypt file if configured. Returns (file_path, was_encrypted)."""
        try:
            encrypted_path = self.encryption_handler.encrypt_file(file_path)
            is_encrypted = encrypted_path != file_path

            if is_encrypted:
                log.info(f"File encrypted: {encrypted_path.name}")

            return encrypted_path, is_encrypted
        except Exception as e:
            log.error("Encryption failed", exc_info=e)
            # Fallback to unencrypted file if encryption fails
            return file_path, False

    def cleanup_encrypted_file(self, file_path: Path) -> None:
        """Securely clean up encrypted temporary files."""
        self.encryption_handler.cleanup_temp_file(file_path)

    @property
    def _matches_retention_config(self):
        """Get retention algorithm - rotation strategies or legacy retention_days."""

        if self.rotation_strategies:
            return partial(
                rotation.matches_crons,
                cron_expressions=[
                    rotation.clean_cron_expression(exp)
                    for exp in self.rotation_strategies
                ],
            )
        else:
            return partial(rotation.within_retention_days, days=Blackbox.retention_days)

    def _do_rotate(self, file_id: str, modified_time: datetime) -> None:
        """Apply retention policy to decide if backup should be deleted or kept."""

        # Check if backup matches any retention rules
        retention_config_matches = self._matches_retention_config(
            dt=modified_time)

        if not retention_config_matches:
            # No retention rules match - delete the backup
            self._delete_backup(file_id=file_id)

        elif self.rotation_strategies:
            # Apply rotation strategy limits to determine if backup should be deleted
            if len(retention_config_matches) == 1:
                # Single matching strategy - use its max directly
                highest_expression = retention_config_matches[0]
                maximum = self.backups_retained[highest_expression]["max"]
            else:
                # Multiple strategies match - use the one with highest retention limit
                highest_expression, maximum = (
                    rotation.get_highest_max_retention_count(
                        retention_tracker=self.backups_retained,
                        cron_expressions=retention_config_matches,
                    ))

            # 🧮 Complex deletion logic: max=0 OR (reached limit AND passed retention window)
            num_retained = self.backups_retained[highest_expression]["num_retained"]
            if rotation.meets_delete_criteria(
                max_to_retain=maximum,
                num_retained=num_retained,
                days=Blackbox.retention_days,
                dt=modified_time,
            ):
                self._delete_backup(file_id=file_id)
            else:
                # Backup retained - increment counters for matching strategies
                for exp in retention_config_matches:
                    self.backups_retained[exp]["num_retained"] += 1

    @abstractmethod
    def _delete_backup(self, file_id: str) -> None:
        """Delete a backup file (storage-specific implementation)."""

    @abstractmethod
    def sync(self, file_path: Path):
        """
        Sync a file to a storage provider.

        All subclasses must implement this method.
        """
        raise NotImplementedError

    @abstractmethod
    def rotate(self, database_id: str):
        """
        Rotate the files in the storage provider.

        This deletes all files older than `rotation_days` days old, as long as
        those files fit certain regular expressions. We don't want to delete
        files that are not related to backup or logging.

        All subclasses must implement this method.
        """
        raise NotImplementedError
