import pytest

from blackbox.exceptions import ImproperlyConfigured
from blackbox.handlers.storage import S3


def test_s3_handler_can_be_instantiated(config_file):
    """Test if the s3 storage handler can be instantiated."""

    with pytest.raises(ImproperlyConfigured):
        # In this case the "aws_secret_access_key" is missing
        S3.config = {
            "user": "internet",
            "password": "dingdong",
            "aws_access_key_id": "somekey",
        }

        S3()
