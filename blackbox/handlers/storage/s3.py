import datetime
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError
from botocore.exceptions import ClientError

from blackbox.config import Blackbox
from blackbox.exceptions import ImproperlyConfigured
from blackbox.handlers.storage._base import BlackboxStorage
from blackbox.utils.logger import log


class S3(BlackboxStorage):
    connstring_regex = r"s3://(?P<bucket_name>[^:]+):(?P<s3_endpoint>[^:]+)"
    valid_prefixes = [
        "s3",
    ]

    def __init__(self):
        super().__init__()

        # Defaults
        self.success = False
        self.output = ""
        self.bucket = self.config.get('bucket_name')

        # If the optional parameters for credentials have been provided, we use these.
        key_id = self.config.get("aws_access_key_id")
        secret_key = self.config.get("aws_secret_access_key")
        s3_endpoint = self.config.get('s3_endpoint')
        configuration = {
            "endpoint_url": f"https://{s3_endpoint}"
        }

        # If config was provided for both of these, we should use it!
        if key_id and secret_key:
            configuration['aws_access_key_id'] = key_id
            configuration['aws_secret_access_key'] = secret_key

        # If config was provided for only one of them, that's too weird of a state for us to accept,
        # so we'll raise an exception. (That weird ^ operator is an XOR).
        elif bool(key_id) ^ bool(secret_key):
            raise ImproperlyConfigured("You must configure either both or none of the AWS credential params.")

        # If neither was provided, we'll just initialize the client without credentials, and
        # it will default to looking at first environment vars and then in ~/.aws/credentials.
        # See https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html
        self.client = boto3.client(
            's3',
            **configuration
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
