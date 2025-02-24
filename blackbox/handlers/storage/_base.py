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
from blackbox.utils.logger import log


# File suffixes considered as an archive
ARCHIVE_SUFFIXES = {".tar", ".zip"}


class BlackboxStorage(BlackboxHandler):
    """An abstract interface for creating Blackbox Storage Providers."""

    handler_type = "storage"

    def __init__(self, **kwargs):
        """Set up storage handler."""
        super().__init__(**kwargs)

        self.success = False  # Was the upload successful?
        self.output = ""     # What did the storage upload output?

        # Enable us to track how many backups matching each strategy have been retained
        self.rotation_strategies = self.config.get("rotation_strategies", [])
        self.backups_retained = rotation.construct_retention_tracker(
            cron_expressions=self.rotation_strategies,
        )

    @staticmethod
    def compress(file_path: Path) -> tuple[typing.IO, bool]:
        """
        Compress the file using gzip into a tempfile.TemporaryFile.

        Returns a two elements tuple.
        The first one is a file-like object, which is removed when it is closed.
        The second one is True if the file has been recompressed, False otherwise.

        This should always be called before syncing the
        file to a storage provider.
        """
        # If the file is already considered as an archive, we don't recompress it
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

    @property
    def _matches_retention_config(self):
        """
        Return the algorithm used for backup retention.

        Ensure backwards compatibility for the old `retention_days` configuration by
        using the retention days algorithm if this configuration is set by the user.
        """

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
        """
        Remove or retain the backup file with the given ID based on rotation strategies.

        Args
            file_id: The unique identifier of the backup file, from the storage system.
                Its format will vary depending on the system. For example, in Google
                Drive, this is the value of the resource's "id" attribute, but in S3,
                this would be the file's Key.
            modified_time: The datetime the file was last modified.
        """

        # Check if we should retain this backup
        retention_config_matches = self._matches_retention_config(
            dt=modified_time)

        if not retention_config_matches:
            # Backup doesn't match any of the retention configs (whether using retention
            # days or rotation strategies) - delete it!
            self._delete_backup(file_id=file_id)

        elif self.rotation_strategies:
            # Determine whether we should delete this backup, based on the rotation
            # strategies config representing the maximum number of backups to retain
            if len(retention_config_matches) == 1:
                # There's only one matching cron/config, so use its max
                highest_expression = retention_config_matches[0]
                maximum = self.backups_retained[highest_expression]["max"]
            else:
                # There are multiple matching crons/configs, find the one with the
                # highest configured max backups to retain, and use this max to
                # determine whether the backup should be deleted
                highest_expression, maximum = (
                    rotation.get_highest_max_retention_count(
                        retention_tracker=self.backups_retained,
                        cron_expressions=retention_config_matches,
                    ))

            # Delete the backup if the following conditions are met:
            #   Configured max is 0
            #   OR We've reached the configured max number of backups
            #   AND
            #   retention_days is not configured
            #   OR retention_days is configured, but the retention window has passed
            num_retained = self.backups_retained[highest_expression]["num_retained"]
            if rotation.meets_delete_criteria(
                max_to_retain=maximum,
                num_retained=num_retained,
                days=Blackbox.retention_days,
                dt=modified_time,
            ):
                self._delete_backup(file_id=file_id)
            else:
                # Otherwise, we've retained the backup, so we should increment the
                # corresponding expression(s) in our retention tracker
                for exp in retention_config_matches:
                    self.backups_retained[exp]["num_retained"] += 1

    @abstractmethod
    def _delete_backup(self, file_id: str) -> None:
        """Delete a backup file."""

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
