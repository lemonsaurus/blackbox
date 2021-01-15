import os
from pathlib import Path

import boto3

from _base import BlackboxStorage


class S3(BlackboxStorage):

    connstring_regex = r"(?P<endpoint>s3://.+)"
    valid_prefixes = [
        "s3",
    ]

    def __init__(self):
        super().__init__()

        # We need to inject the access keys from the connstring into the environment
        # variables named AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY.
        #
        # However, if these environment variables are already set, we should set them back
        # to what they were after we're done, so we don't mess with the local environment.
        #
        # If they're _not_ currently set, we should unset them after we're done. Basically
        # this whole environment variable modification stuff needs to be idempotent.
        self.access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
        self.secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")

        os.environ["AWS_ACCESS_KEY_ID"] = self.config.get("aws_access_key_id")
        os.environ["AWS_SECRET_ACCESS_KEY"] = self.config.get("aws_secret_access_key")

    def teardown(self):
        """Restore environment variables to their former state."""
        if self.access_key_id:
            os.environ["AWS_ACCESS_KEY_ID"] = self.access_key_id
        else:
            del os.environ["AWS_ACCESS_KEY_ID"]

        if self.secret_access_key:
            os.environ["AWS_SECRET_ACCESS_KEY"] = self.secret_access_key
        else:
            del os.environ["AWS_SECRET_ACCESS_KEY"]

    def sync(self, file_path: Path) -> None:
        """Sync a file to an S3 bucket."""
        raise NotImplementedError

    def rotate(self) -> None:
        """
        Rotate the files in the S3 bucket.

        This deletes all files older than `config.BlackBox.retention_days` days old, as long as
        those files fit certain regular expressions. We don't want to delete
        files that are not related to backup or logging.
        """
        raise NotImplementedError
