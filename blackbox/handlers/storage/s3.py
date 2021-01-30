import datetime
import os
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError
from botocore.exceptions import ClientError

from blackbox.config import Blackbox
from blackbox.exceptions import ImproperlyConfigured
from blackbox.handlers.storage._base import BlackboxStorage
from blackbox.utils.logger import log


class S3(BlackboxStorage):
    connstring_regex = r"s3://(?P<bucket_name>[^:]+):(?P<s3_endpoint>[^:?]+)"
    valid_prefixes = [
        "s3",
    ]

    def __init__(self):
        super().__init__()

        # We don't need to initialize handlers that aren't enabled.
        if not self.enabled:
            return

        # Defaults
        self.success = False
        self.output = ""
        self.bucket = self.config.get('bucket_name')

        # If the optional parameters for credentials have been provided, we use these.
        key_id = self.config.get("aws_access_key_id")
        secret_key = self.config.get("aws_secret_access_key")
        s3_endpoint = self.config.get('s3_endpoint')
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
            raise ImproperlyConfigured("You must configure either both or none of the S3 credential params.")

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
        self.client = self.session.client(
            's3',
            endpoint_url=f"https://{s3_endpoint}",
        )

    def sync(self, file_path: Path) -> None:
        """Sync a file to an S3 bucket."""
        file_ = self.compress(file_path)

        try:
            self.client.upload_fileobj(
                file_,
                self.bucket,
                file_path.name,
            )
            self.success = True
        except (ClientError, BotoCoreError) as e:
            log.error(e)
            self.output = str(e)
            self.success = False

    def rotate(self) -> None:
        """
        Rotate the files in the S3 bucket.

        This deletes all files older than `config.BlackBox.retention_days` days old, as long as
        those files fit certain regular expressions. We don't want to delete
        files that are not related to backup or logging.
        """
        retention_days = Blackbox.retention_days

        # Look through the items and figure out which ones are older than `retention_days`.
        # Catch all boto errors and log them to avoid return code 1.
        try:
            for item in self.client.list_objects(Bucket=self.bucket)["Contents"]:
                last_modified = item.get("LastModified")
                now_tz = datetime.datetime.now(tz=last_modified.tzinfo)
                delta = now_tz - item.get("LastModified")

                # Delete the deprecated items
                if delta.days >= retention_days:
                    self.client.delete_object(
                        Bucket=self.bucket,
                        Key=item.get("Key")
                    )
        except (ClientError, BotoCoreError) as e:
            log.error(e)
