from datetime import datetime
from pathlib import Path

from dropbox import Dropbox as DropboxClient
from dropbox.exceptions import ApiError
from dropbox.exceptions import HttpError
from dropbox.files import CommitInfo
from dropbox.files import FileMetadata
from dropbox.files import UploadSessionCursor
from dropbox.files import WriteMode

from blackbox.config import Blackbox
from blackbox.handlers.storage._base import BlackboxStorage
from blackbox.utils.logger import log


class Dropbox(BlackboxStorage):
    """Storage handler that uploads backups to Dropbox."""

    connstring_regex = r"dropbox://(?P<access_token>[^?]+)"
    valid_prefixes = [
        "dropbox"
    ]

    def __init__(self):
        super().__init__()

        # We don't need to initialize handlers that aren't enabled.
        if not self.enabled:
            return

        self.success = False
        self.output = ""

        self.upload_base = self.config.get("upload_directory") or "/"
        self.client = DropboxClient(self.config.get("access_token"))

    def sync(self, file_path: Path) -> None:
        """Sync a file to Dropbox."""
        # This is size what can be uploaded as one chunk.
        # When file is bigger than that, this will be uploaded
        # in multiple parts.
        chunk_size = 4 * 1024 * 1024

        upload_path = f"{self.upload_base}{file_path.name}"

        try:
            with file_path.open("rb") as f:
                file_size = file_path.stat().st_size
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

    def rotate(self) -> None:
        """
        Rotate the files in the Dropbox directory.

        All files in base directory of backups will be deleted when they
        are older than `retention_days`, and because of this,
        it's better to have backups in isolated folder.
        """
        # Receive first batch of files.
        files_result = self.client.files_list_folder(
            self.upload_base if self.upload_base != "/" else ""
        )
        entries = [
            entry for entry in files_result.entries if isinstance(entry, FileMetadata)
        ]

        # If there is more files, receive all of them.
        while files_result.has_more:
            cursor = files_result.cursor
            files_result = self.client.files_list_folder_continue(cursor)
            entries += [
                entry for entry in files_result.entries if isinstance(entry, FileMetadata)
            ]

        # Find all old files and delete them.
        for item in entries:
            last_modified = item.server_modified
            now = datetime.now(tz=last_modified.tzinfo)
            delta = now - last_modified

            if delta.days >= Blackbox.retention_days:
                self.client.files_delete(item.path_lower)
