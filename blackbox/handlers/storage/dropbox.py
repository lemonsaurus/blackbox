import os
import re
from pathlib import Path

from dropbox import Dropbox as DropboxClient
from dropbox.exceptions import ApiError
from dropbox.exceptions import AuthError
from dropbox.exceptions import HttpError
from dropbox.files import CommitInfo
from dropbox.files import FileMetadata
from dropbox.files import UploadSessionCursor
from dropbox.files import WriteMode

from blackbox.handlers.storage._base import BlackboxStorage
from blackbox.utils.logger import log


class Dropbox(BlackboxStorage):
    """Storage handler that uploads backups to Dropbox."""

    required_fields = ("access_token",)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.upload_base = self.config.get("upload_directory") or "/"
        self.client = DropboxClient(self.config["access_token"])
        self.valid = self._validate_token()

    def _validate_token(self):
        """Check if dropbox token is valid."""
        try:
            # Try to get current account info to validate token
            self.client.users_get_current_account()
            return True
        except (AuthError, ApiError, HttpError):
            return False

    def _delete_backup(self, file_id: str) -> None:
        """
        Delete a backup file.

        Args
            file_id: The file's identifier. For Dropbox, this would be the file path.
        """

        self.client.files_delete(path=file_id)

    def sync(self, file_path: Path) -> None:
        """Sync a file to Dropbox."""
        # Check if Dropbox token is valid.
        if self.valid is False:
            error = "Dropbox token is invalid!"
            self.success = False
            self.output = error
            log.error(error)
            return None

        # This is size what can be uploaded as one chunk.
        # When file is bigger than that, this will be uploaded
        # in multiple parts.
        chunk_size = 4 * 1024 * 1024

        temp_file, recompressed = self.compress(file_path)
        upload_path = f"{self.upload_base}{file_path.name}{'.gz' if recompressed else ''}"

        try:
            with temp_file as f:
                file_size = os.stat(f.name).st_size
                log.debug(file_size)
                if file_size <= chunk_size:
                    self.client.files_upload(
                        f.read(), upload_path, WriteMode.overwrite
                    )
                else:
                    session_start = self.client.files_upload_session_start(
                        f.read(chunk_size)
                    )
                    cursor = UploadSessionCursor(
                        session_start.session_id,
                        offset=f.tell()
                    )
                    # Commit contains path in Dropbox and write mode about file
                    commit = CommitInfo(upload_path, WriteMode.overwrite)

                    while f.tell() < file_size:
                        if (file_size - f.tell()) <= chunk_size:
                            self.client.files_upload_session_finish(
                                f.read(chunk_size),
                                cursor,
                                commit
                            )
                        else:
                            self.client.files_upload_session_append(
                                f.read(chunk_size),
                                cursor.session_id,
                                cursor.offset
                            )
                            cursor.offset = f.tell()
            self.success = True
        except (ApiError, HttpError) as e:
            log.error(e)
            self.success = False
            self.output = str(e)

    def rotate(self, database_id: str) -> None:
        """
        Rotate the files in the Dropbox directory.

        All files in base directory of backups will be deleted when they
        are older than `retention_days`, and because of this,
        it's better to have backups in isolated folder.
        """
        # Check if Dropbox token is valid.
        if self.valid is False:
            log.error("Dropbox token is invalid - Can't delete old backups!")
            return None
        # Let's rotate only this type of database
        db_type_regex = rf"{database_id}_blackbox_\d{{2}}_\d{{2}}_\d{{4}}.+"

        # Receive first batch of files.
        files_result = self.client.files_list_folder(
            self.upload_base if self.upload_base != "/" else ""
        )
        entries = [entry for entry in files_result.entries if
                   self._is_backup_file(entry, db_type_regex)]

        # If there is more files, receive all of them.
        while files_result.has_more:
            cursor = files_result.cursor
            files_result = self.client.files_list_folder_continue(cursor)
            entries += [entry for entry in files_result.entries if
                        self._is_backup_file(entry, db_type_regex)]

        # Sort the backups in order of most recent to last.
        entries = sorted(
            entries,
            key=lambda entry: entry.server_modified,
            reverse=True,
        )

        # Find all old files and delete them.
        for item in entries:
            last_modified = item.server_modified
            self._do_rotate(file_id=item.path_lower, modified_time=last_modified)

    @staticmethod
    def _is_backup_file(entry, db_type_regex) -> bool:
        """Check if file is actually this kind of database backup."""
        return isinstance(entry, FileMetadata) and re.match(db_type_regex, entry.name)
