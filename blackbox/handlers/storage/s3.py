import os
import re
import tempfile
from pathlib import Path
from typing import BinaryIO
from typing import Optional
from typing import Tuple

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

    def _prepare_compressed_file(self, file_path: Path,
                                 compressed_file: BinaryIO) -> Tuple[Path, bool]:
        """
        Prepare compressed file for encryption by creating a temporary file.

        Returns:
            Tuple of (temp_file_path, is_encrypted)
        """
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=f"-{file_path.name}.gz"
        )
        temp_file_path = Path(temp_file.name)

        # Copy compressed data to temp file
        compressed_file.seek(0)
        temp_file.write(compressed_file.read())
        temp_file.close()
        compressed_file.close()

        # Encrypt the compressed temp file
        encrypted_path, is_encrypted = self.encrypt_file(temp_file_path)
        return encrypted_path if is_encrypted else temp_file_path, is_encrypted

    def _determine_filename(self, original_name: str, is_compressed: bool,
                            is_encrypted: bool) -> str:
        """Determine the final filename based on compression and encryption status."""
        if is_compressed and is_encrypted:
            return f"{original_name}.gz.enc"
        elif is_compressed:
            return f"{original_name}.gz"
        elif is_encrypted:
            return f"{original_name}.enc"
        else:
            return original_name

    def _cleanup_temp_files(self, temp_file_path: Optional[Path],
                            encrypted_path: Optional[Path], is_encrypted: bool) -> None:
        """Clean up temporary and encrypted files."""
        if temp_file_path and temp_file_path.exists():
            temp_file_path.unlink()
        if is_encrypted and encrypted_path and encrypted_path.exists():
            self.cleanup_encrypted_file(encrypted_path)

    def sync(self, file_path: Path) -> None:
        """Sync a file to an S3 bucket."""
        file_, recompressed = self.compress(file_path)

        encrypted_path = None
        is_encrypted = False
        temp_file_path = None
        final_file: Optional[BinaryIO] = None

        try:
            if recompressed:
                final_file_path, is_encrypted = self._prepare_compressed_file(file_path, file_)
                temp_file_path = final_file_path if not is_encrypted else Path(file_.name)
                if is_encrypted:
                    encrypted_path = final_file_path
                final_file = open(final_file_path, 'rb')
            else:
                # Encrypt original file directly
                encrypted_path, is_encrypted = self.encrypt_file(file_path)
                if is_encrypted:
                    file_.close()
                    final_file = open(encrypted_path, 'rb')
                else:
                    final_file = file_

            final_filename = self._determine_filename(file_path.name, recompressed, is_encrypted)

            extra_args = {}
            if recompressed and not is_encrypted:
                extra_args["ContentEncoding"] = "gzip"

            self.client.upload_fileobj(
                final_file,
                self.bucket,
                final_filename,
                ExtraArgs=extra_args
            )
            self.success = True

        except (ClientError, BotoCoreError) as e:
            log.error(e)
            self.output = str(e)
            self.success = False
        finally:
            if final_file:
                final_file.close()
            self._cleanup_temp_files(temp_file_path, encrypted_path, is_encrypted)

    def rotate(self, database_id: str) -> None:
        """
        Rotate the files in the S3 bucket.

        This deletes all files older than `config.BlackBox.retention_days` days old, as long as
        those files fit certain regular expressions. We don't want to delete
        files that are not related to backup or logging.
        """
        from blackbox.config import Blackbox
        rotation_patterns = Blackbox.get_rotation_patterns(database_id)

        # Get files object from remote S3 bucket.
        remote_objects = self.client.list_objects_v2(Bucket=self.bucket).get("Contents")

        # Filter their names with only this kind of database, sorted in order of last
        # modified datetime, with the most recent backups first.
        relevant_backups = sorted(
            [
                item for item in remote_objects
                if any(re.match(pattern, item.get("Key")) for pattern in rotation_patterns)
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
