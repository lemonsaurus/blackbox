"""Google Drive database backup storage integration."""
import mimetypes
import re
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional
from typing import Union

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload

from blackbox.handlers.storage._base import BlackboxStorage
from blackbox.utils.logger import log


class GoogleDrive(BlackboxStorage):
    """Storage handler that uploads backups to Google Drive."""

    required_fields = ("refresh_token", "client_id", "client_secret")

    @staticmethod
    def clean_upload_directory(upload_directory: str) -> str:
        """
        Clean up the provided upload directory path string.

        Leading and trailing slashes will be removed. Duplicate slashes will be cleaned
        up, so that no slash can exist directly beside another one.

        Example input: /Hello//World///
        Example output: Hello/World
        """

        # Clean up duplicate slashes
        while "//" in upload_directory:
            upload_directory = upload_directory.replace("//", "/")
        # Strip leading slash
        if upload_directory.startswith("/"):
            upload_directory = upload_directory[1:]
        # Strip trailing slash
        if upload_directory.endswith("/"):
            upload_directory = upload_directory[:-1]
        return upload_directory

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # The upload base path should not have a leading or trailing slash, but in case
        # it does, let's ensure we strip those away.
        upload_directory = self.config.get("upload_directory") or ""
        self.upload_base = GoogleDrive.clean_upload_directory(upload_directory)

        # Get credentials and initialize the Google Drive API client
        self.oauth_uri = "https://oauth2.googleapis.com/token"
        self.refresh_token = self.config["refresh_token"]
        self.client_id = self.config["client_id"]
        self.client_secret = self.config["client_secret"]
        self._initialize_drive_client()

    def _initialize_drive_client(self) -> None:
        """Initialize the Google API Python client."""
        # Build the Credentials object required for initializing the client
        self.credentials = Credentials(
            None,  # No access token initially
            refresh_token=self.refresh_token,
            client_id=self.client_id,
            client_secret=self.client_secret,
            token_uri=self.oauth_uri,
        )
        # Refresh the access token to authenticate API requests
        self.credentials.refresh(Request())
        # Establish the Google Drive client
        self.client: Resource = build("drive", "v3", credentials=self.credentials)

    def _find_folder(self, folder_path: str, parent_id: str = "root") -> Optional[dict]:
        """
        Search for an existing folder by path within a specific parent.

        Args
            folder_path: The path to the folder.
            parent_id: The ID of the parent folder. Default is "root".

        Return
            The folder matching the provided path, or None if it wasn't found.
        """

        folder_names = folder_path.split("/")
        current_path: list[str] = []  # Track how far along we've gone down the path
        last_folder_found = None

        for folder_name in folder_names:
            # No need to make a request if `folder_name` is an empty string. The path
            # should be cleaned to strip leading/trailing/duplicate slashes before
            # calling this function, so we shouldn't encounter this, but it's good to
            # have a fallback, just in case.
            if not len(folder_name):
                continue
            # Search for folders with this name, of type folder, that are not in the
            # trash, and who have the provided parent folder ID as an ancestor
            query = (
                f"name='{folder_name}' "
                f"and mimeType='application/vnd.google-apps.folder' "
                f"and trashed=false and '{parent_id}' in parents"
            )
            response = self.client.files().list(
                q=query,
                spaces="drive",
                fields="files(id, name, parents)",
            ).execute()
            folders = response.get("files", [])
            if folders:
                parent_id = folders[0]["id"]
                last_folder_found = folders[0]
                current_path.append(folder_name)
            else:
                break

        if current_path == folder_names:
            return last_folder_found
        return None

    def _create_folder(self, folder_path: str, parent_id: str = "root") -> str:
        """
        Create a folder in Google Drive if it does not already exist.

        Args
            folder_path: The path to the folder.
            parent_id: The ID of the parent folder. Default is "root".

        Return
            The ID of the created folder, or the ID of the folder with the given path
            if it already exists.
        """

        last_folder_id = parent_id
        folder_names = folder_path.split("/")
        for folder_name in folder_names:
            # Check if a folder with this path already exists by searching for it
            if existing_folder := self._find_folder(
                folder_path=folder_name,
                parent_id=last_folder_id,
            ):
                last_folder_id = existing_folder.get("id")
                continue
            # The folder doesn't exist, so let's create it!
            metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [last_folder_id],
            }
            folder = self.client.files().create(
                body=metadata,
                fields="id",
            ).execute()
            last_folder_id = folder.get("id")
        return last_folder_id

    def _get_and_ensure_deepest_folder_id(self, path: str) -> str:
        """
        Get the ID of the deepest folder in the provided path.

        Any folders in the path that do not already exist will be created.

        Args
            path: The folder path, excluding a file.

        Return
            The ID of the deepest folder.
        """

        folder = self._find_folder(path)
        if not folder:
            parent_id = "root"
            return self._create_folder(
                folder_path=path,
                parent_id=parent_id,
            )
        else:
            return folder["id"]

    def _upload(self, file_path: str, file_content: Union[bytes, str]) -> str:
        """
        Upload a file to Google Drive.

        Args
            file_path: The path to upload the file to.
            file_content: The content of the file to upload.

        Return
            The ID of the uploaded file.
        """

        # Determine the MIME type of the file, because we need to include this in the
        # payload when we upload the file to Google Drive.
        mimetype, _ = mimetypes.guess_type(file_path)

        # Get the folder
        folder_id = "root"  # Use the root folder as a default
        folder_path = "/".join(file_path.split("/")[:-1])  # Path excluding filename
        if self.upload_base:
            folder_id = self._get_and_ensure_deepest_folder_id(path=folder_path)

        # Prepare the file metadata
        file_name = file_path.split("/")[-1]
        file_metadata = {"name": file_name, "parents": [folder_id]}

        # Upload the file to Google Drive
        # The size of one chunk. Larger files will be uploaded in multiple chunks.
        chunk_size = 4950000  # 5 MB limit, let's stay a bit under for safety
        file_io = BytesIO(file_content)
        media = MediaIoBaseUpload(
            file_io,
            chunksize=chunk_size,
            mimetype=mimetype,
            resumable=True,  # Allow this upload to occur in multiple parts
        )
        response = self.client.files().create(
            body=file_metadata,
            media_body=media,
            fields="id",
        ).execute()
        return response["id"]

    def _delete_backup(self, file_id: str) -> None:
        """Delete a backup file."""
        self.client.files().delete(fileId=file_id).execute()

    def sync(self, file_path: Path) -> None:
        """Sync a file to Google Drive."""
        # Compress the file and build the destination file path
        temp_file, recompressed = self.compress(file_path)
        ext = ".gz" if recompressed else ""
        upload_path = f"{self.upload_base}/{file_path.name}{ext}"
        try:
            with temp_file as f:
                # Upload the file
                self._upload(file_path=upload_path, file_content=f.read())
            self.success = True
        except HttpError as e:
            log.error(e)
            self.success = False
            self.output = str(e)

    def rotate(self, database_id: str) -> None:
        """
        Rotate the files in the Google Drive directory.

        All files in the base directory of backups will be deleted when they are older
        than `retention_days`. Because of this, it's better to store backups in an
        isolated folder.
        """

        # Get the folder
        folder_id = "root"  # Default to the root folder
        if self.upload_base:
            folder_id = self._get_and_ensure_deepest_folder_id(path=self.upload_base)

        # Fetch database backup files
        from blackbox.config import Blackbox
        rotation_patterns = Blackbox.get_rotation_patterns(database_id)
        query = f"'{folder_id}' in parents and name contains 'blackbox'"
        try:
            response = self.client.files().list(
                q=query,
                spaces="drive",
                fields="files(id, name, modifiedTime)",
                orderBy="modifiedTime desc",  # Order by most recent backup
            ).execute()
            files = response.get("files", [])

        except HttpError as e:
            log.error(e)
            self.success = False
            self.output = str(e)

        else:
            # Delete database backups that do not match the user's retention config
            for file_ in files:
                if any(re.match(pattern, file_["name"]) for pattern in rotation_patterns):
                    last_modified = file_["modifiedTime"]
                    modified_time = datetime.fromisoformat(
                        last_modified.replace("Z", "+00:00"))
                    self._do_rotate(file_id=file_["id"], modified_time=modified_time)
            self.success = True
