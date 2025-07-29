import contextlib
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
    """Storage handler for S3-compatible APIs (AWS S3, Backblaze B2, etc)."""

    required_fields = ("bucket", "endpoint")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.bucket = self.config["bucket"]
        self.endpoint = self.config["endpoint"]

        # Use provided credentials if both key_id and secret_key are given
        key_id = self.config.get("aws_access_key_id")
        secret_key = self.config.get("aws_secret_access_key")
        configuration = dict()

        # Both credentials provided - use them
        if key_id and secret_key:
            configuration = {
                "aws_access_key_id": key_id,
                "aws_secret_access_key": secret_key,
            }

        # ⚠️ Only one credential provided - invalid configuration (XOR check)
        elif bool(key_id) ^ bool(secret_key):
            raise ImproperlyConfigured(
                "You must configure either both or none of the S3 credential params.")

        else:
            # No explicit credentials - check environment variables and ~/.aws/ files
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

        # Credentials found - proceed with boto3 session creation
        self.session = boto3.Session(
            **configuration
        )

        # Custom client config support (e.g., Backblaze B2 compatibility)
        client_config = self.config.get("client_config")
        if client_config is not None:
            # Convert dict config to boto3 Config object
            if isinstance(client_config, dict):
                client_config = Config(**client_config)

        self.client = self.session.client(
            's3',
            endpoint_url=f"https://{self.endpoint}",
            config=client_config,
        )

    def _delete_backup(self, file_id: str) -> None:
        """🗑️ Delete S3 object by Key."""

        self.client.delete_object(Bucket=self.bucket, Key=file_id)

    def _prepare_compressed_file(self, file_path: Path,
                                 compressed_file: BinaryIO) -> Tuple[Path, bool]:
        """Create temp file from compressed data and encrypt if configured."""
        temp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=f"-{file_path.name}.gz"
        )
        temp_file_path = Path(temp_file.name)

        # Copy compressed data to temporary file
        compressed_file.seek(0)
        temp_file.write(compressed_file.read())
        temp_file.close()
        compressed_file.close()

        # Encrypt the compressed temporary file
        encrypted_path, is_encrypted = self.encrypt_file(temp_file_path)
        return encrypted_path if is_encrypted else temp_file_path, is_encrypted

    def _determine_filename(self, original_name: str, is_compressed: bool,
                            is_encrypted: bool) -> str:
        """Build filename with .gz and/or .enc extensions as needed."""
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
        """Clean up temporary and encrypted files safely."""
        if temp_file_path and temp_file_path.exists():
            temp_file_path.unlink()
        if is_encrypted and encrypted_path and encrypted_path.exists():
            self.cleanup_encrypted_file(encrypted_path)

    def sync(self, file_path: Path) -> None:
        """Upload file to S3 bucket with compression and encryption as configured."""
        file_, recompressed = self.compress(file_path)

        encrypted_path = None
        is_encrypted = False
        temp_file_path = None

        try:
            if recompressed:
                final_file_path, is_encrypted = self._prepare_compressed_file(file_path, file_)
                temp_file_path = final_file_path if not is_encrypted else None
                if is_encrypted:
                    encrypted_path = final_file_path

                # Safe file handling with context manager
                with open(final_file_path, 'rb') as final_file:
                    final_filename = self._determine_filename(
                        file_path.name, recompressed, is_encrypted
                    )
                    extra_args = {}
                    if recompressed and not is_encrypted:
                        extra_args["ContentEncoding"] = "gzip"

                    self.client.upload_fileobj(
                        final_file,
                        self.bucket,
                        final_filename,
                        ExtraArgs=extra_args
                    )
            else:
                # Encrypt original file without recompression
                encrypted_path, is_encrypted = self.encrypt_file(file_path)

                # Determine upload filename and use safe file handling
                final_filename = self._determine_filename(
                    file_path.name, recompressed, is_encrypted
                )

                # Close compressed file handle before proceeding
                if not is_encrypted:
                    file_.close()
                    with open(file_path, 'rb') as upload_file:
                        self.client.upload_fileobj(
                            upload_file,
                            self.bucket,
                            final_filename
                        )
                else:
                    file_.close()
                    with open(encrypted_path, 'rb') as upload_file:
                        self.client.upload_fileobj(
                            upload_file,
                            self.bucket,
                            final_filename
                        )

            self.success = True

        except (ClientError, BotoCoreError) as e:
            log.error(e)
            self.output = str(e)
            self.success = False
        finally:
            # Ensure compressed file handle is properly closed
            if hasattr(file_, 'close'):
                with contextlib.suppress(Exception):
                    file_.close()
            self._cleanup_temp_files(temp_file_path, encrypted_path, is_encrypted)

    def rotate(self, database_id: str) -> None:
        """Delete old backups from S3 bucket based on retention policies."""
        from blackbox.config import Blackbox
        rotation_patterns = Blackbox.get_rotation_patterns(database_id)

        # Fetch all objects from S3 bucket
        remote_objects = self.client.list_objects_v2(Bucket=self.bucket).get("Contents")

        # Filter to database-specific backups, sorted by modification time (newest first)
        relevant_backups = sorted(
            [
                item for item in remote_objects
                if any(re.match(pattern, item.get("Key")) for pattern in rotation_patterns)
            ],
            key=lambda obj: obj.get("LastModified"),
            reverse=True,
        )

        # 🗑️ Apply retention policy to each backup (catch boto errors to avoid exit code 1)
        try:
            for item in relevant_backups:
                last_modified = item.get("LastModified")
                self._do_rotate(file_id=item.get("Key"), modified_time=last_modified)
        except (ClientError, BotoCoreError) as e:
            log.error(e)
