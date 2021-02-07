import json
import os

import pytest

from blackbox.exceptions import ImproperlyConfigured
from blackbox.handlers.storage import S3


def test_s3_missing_aws_file(config_file):
    """Test raising ImproperlyConfigured when the aws config file is missing."""

    with pytest.raises(ImproperlyConfigured):
        # In this case the "aws_secret_access_key" is missing
        S3()


def test_s3_endpoint(config_file, mocker):
    """Test if the s3 storage handler can be instantiated with environment variables."""

    os.environ["aws_access_key_id"] = "some"
    os.environ["aws_secret_access_key"] = "key"
    S3.config = {
        "username": "john",
        "password": "mcgee",
        "s3_endpoint": "s3://s3.endpoint.com/",
        "bucket_name": "bucket"
    }

    data = json.dumps({
        "partitions": [{
            "defaults": {
                "hostname": r"{service}.{region}.{dnsSuffix}",
                "protocols": ["https"],
                "signatureVersions": ["v4"],
                "serviceId": "myservice"
            },
            "dnsSuffix": "amazonaws.com",
            "partition": "aws",
            "partitionName": "AWS Standard",
            "regionRegex": r"^(us|eu|ap|sa|ca|me|af)\-\w+\-\d+$",
            "regions": {
                "eu-central-1": {
                    "description": "Europe (Frankfurt)"
                },
            }
        }]
    })

    mocker.patch("builtins.open", mocker.mock_open(read_data=data.encode()))

    S3()
