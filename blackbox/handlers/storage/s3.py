import os
import re
from pathlib import Path

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError
from botocore.exceptions import ClientError

from blackbox.exceptions import ImproperlyConfigured
from blackbox.handlers.storage._base import BlackboxStorage
from blackbox.utils.logger import log


class S3(BlackboxStorage):
    """A storage handler for S3-compatible APIs."""

    required_fields = ("bucket", "endpoint")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.bucket = self.config["bucket"]
        self.endpoint = self.config["endpoint"]

        # If the optional parameters for credentials have been provided, we use these.
        key_id = self.config.get("aws_access_key_id")
        secret_key = self.config.get("aws_secret_access_key")
        configuration = dict()

        # If config was provided for both of these, we should use it!
        if key_id and secret_key:
            configuration = {
                "aws_access_key_id": key_id,
                "aws_secret_access_key": secret_key,
            }

        # If config was provided for only one of them, that's too weird of a state for us to accept,
        # so we'll raise an exception. (That weird ^ operator is an XOR).
        elif bool(key_id) ^ bool(secret_key):
            raise ImproperlyConfigured(
                "You must configure either both or none of the S3 credential params.")

        else:
            # If config hasn't been provided, we expect either environment variables or ~/.aws/
            # credentials and config files to exist. If none of that exists, we should raise
            # a convenient error.
            has_environment_variables = (
                os.environ.get("AWS_ACCESS_KEY_ID")
                and os.environ.get("AWS_SECRET_ACCESS_KEY")
            )
            has_aws_config_files = (
                (Path.home() / ".aws/config").exists()
                and (Path.home() / ".aws/credentials").exists()
            )
            if not has_aws_config_files and not has_environment_variables:
                raise ImproperlyConfigured(
                    "Blackbox could not find any valid S3 credentials. "
                    "See the readme under Configuration for more information on how to do this."
                )

        # If we get to this point, the user has either environment variables or credentials files,
        # so Blackbox will make use of these.
        # See https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html
        self.session = boto3.Session(
            **configuration
        )

        # Support for custom client configuration (e.g., for Backblaze B2 compatibility)
        client_config = self.config.get("client_config")
        if client_config is not None:
            # Convert dict to Config object if needed
            if isinstance(client_config, dict):
                client_config = Config(**client_config)

        self.client = self.session.client(
            's3',
            endpoint_url=f"https://{self.endpoint}",
            config=client_config,
        )

    def _delete_backup(self, file_id: str) -> None:
        """
        Delete a backup file.

        Args
            file_id: The identifier of the file. For S3, this would be its Key.
        """

        self.client.delete_object(Bucket=self.bucket, Key=file_id)

    def sync(self, file_path: Path) -> None:
        """Sync a file to an S3 bucket."""
        file_, recompressed = self.compress(file_path)

        try:
            self.client.upload_fileobj(
                file_,
                self.bucket,
                f"{file_path.name}{'.gz' if recompressed else ''}",
                ExtraArgs={"ContentEncoding": "gzip"}
            )
            self.success = True
        except (ClientError, BotoCoreError) as e:
            log.error(e)
            self.output = str(e)
            self.success = False

    def rotate(self, database_id: str) -> None:
        """
        Rotate the files in the S3 bucket.

        This deletes all files older than `config.BlackBox.retention_days` days old, as long as
        those files fit certain regular expressions. We don't want to delete
        files that are not related to backup or logging.
        """
        db_type_regex = rf"{database_id}_blackbox_\d{{2}}_\d{{2}}_\d{{4}}.+"

        # Get files object from remote S3 bucket.
        remote_objects = self.client.list_objects_v2(Bucket=self.bucket).get("Contents")

        # Filter their names with only this kind of database, sorted in order of last
        # modified datetime, with the most recent backups first.
        relevant_backups = sorted(
            [
                item for item in remote_objects
                if re.match(db_type_regex, item.get("Key"))
            ],
            key=lambda obj: obj.get("LastModified"),
            reverse=True,
        )

        # Look through the items and figure out which ones are older than `retention_days`.
        # Catch all boto errors and log them to avoid return code 1.
        try:
            for item in relevant_backups:
                last_modified = item.get("LastModified")
                self._do_rotate(file_id=item.get("Key"), modified_time=last_modified)
        except (ClientError, BotoCoreError) as e:
            log.error(e)
