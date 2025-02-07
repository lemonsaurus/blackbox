"""Google Drive database backup storage integration."""
from io import BytesIO
import mimetypes
from datetime import datetime
from pathlib import Path
import re

from blackbox.config import Blackbox
from blackbox.handlers.storage._base import BlackboxStorage
from blackbox.utils.logger import log

from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials


class GoogleDrive(BlackboxStorage):
    """Storage handler that uploads backups to Google Drive."""

    required_fields = ("refresh_token", "client_id", "client_secret")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # The upload base path should not have a leading or trailing slash
        self.upload_base = self.config.get("upload_directory") or ""

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

    def _find_folder(self, folder_path: str, parent_id: str = "root") -> str | None:
        """
        Search for an existing folder by path within a specific parent.

        Args
            folder_path: The path to the folder. It does not matter if there is a
                         leading or trailing slash.
            parent_id: The ID of the parent folder. Default is "root".

        Return
            The ID of the found folder, or None if no folder was found.
        """

        folder_names = folder_path.split("/")
        last_folder_found = None
        for folder_name in folder_names:
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
                fields="files(id, name)",
            ).execute()
            folders = response.get("files", [])
            if folders:
                parent_id = folders[0]["id"]
                last_folder_found = folders[0]
            else:
                break

        return last_folder_found

    def _create_folder(self, folder_path: str, parent_id: str = "root") -> str:
        """
        Create a folder in Google Drive.

        Important note: If a folder with this name already exists, another will be
        created. The original will not be overwritten.

        Args
            folder_path: The path to the folder. It does not matter if there is a
                         leading or trailing slash.
            parent_id: The ID of the parent folder. Default is "root".

        Return
            The ID of the created folder.
        """

        folder_names = folder_path.split("/")
        for folder_name in folder_names:
            metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder",
                "parents": [parent_id],
            }
            folder = self.client.files().create(
                body=metadata,
                fields="id",
            ).execute()
            parent_id = folder.get("id")
        return parent_id
    
    def _get_and_ensure_deepest_folder_id(self, path: str) -> str:
        """
        Get the ID of the deepest folder in the provided path.

        Any folders in the path that do not already exist will be created.

        Args
            path: The folder path, excluding a file. It does not matter if there is a
                  leading or trailing slash.
        
        Return
            The ID of the deepest folder.
        """

        deepest_folder = path.split("/")[-1]  # Get the last part of the path
        folder = self._find_folder(path)  # Get the folder object from Google Drive
        if not folder or folder["name"] != deepest_folder:
            # Create all folders in the path if none exist. Otherwise, only create
            # the ones that don't exist yet.
            new_folder_path = path if not folder else path.split(folder["name"])[1]
            parent_id = "root" if not folder else folder["id"]
            return self._create_folder(
                folder_path=new_folder_path,
                parent_id=parent_id,
            )
        else:
            return folder["id"]

    def _upload(self, file_path: str, file_content: bytes | str) -> str:
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

        retention_days = 7  # Default
        if Blackbox.retention_days:
            retention_days = Blackbox.retention_days  # Overwrite if this is configuired

        # Get the folder (remove the trailing slash from the base folder)
        folder_id = "root"  # Default to the root folder
        if self.upload_base:
            folder_id = self._get_and_ensure_deepest_folder_id(path=self.upload_base)

        # Fetch database backup files
        db_type_regex = rf"{database_id}_blackbox_\d{{2}}_\d{{2}}_\d{{4}}.+"
        query = f"'{folder_id}' in parents and name contains 'blackbox'"
        try:
            response = self.client.files().list(
                q=query,
                spaces="drive",
                fields="files(id, name, modifiedTime)",
            ).execute()
            files = response.get("files", [])
        except HttpError as e:
            log.error(e)
            self.success = False
            self.output = str(e)
        else:
            # Delete database backups that are older than the configured retention days
            for file_ in files:
                if re.match(db_type_regex, file_['name']):
                    last_modified = file_["modifiedTime"]
                    modified_time = datetime.fromisoformat(
                        last_modified.replace("Z", "+00:00"))
                    now = datetime.now(tz=modified_time.tzinfo)
                    delta = now - modified_time
                    if delta.days >= retention_days:
                        self.client.files().delete(fileId=file_["id"]).execute()
            self.success = True
