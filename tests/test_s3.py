import pytest

from blackbox.exceptions import MissingFields
from blackbox.handlers.storage import S3


@pytest.fixture
def mock_valid_s3_config():
    return {"bucket": "bigbucket", "endpoint": "s3.endpoint.com"}


@pytest.fixture
def mock_invalid_s3_config():
    return {"bucket": "smolbucket"}


def test_s3_handler_can_be_instantiated_with_required_fields(mock_valid_s3_config):
    """Test if the s3 storage handler can be instantiated."""
    S3(**mock_valid_s3_config)


def test_s3_handler_fails_without_required_fields(mock_invalid_s3_config):
    """Test if the s3 storage handler cannot be instantiated with missing fields."""
    with pytest.raises(MissingFields):
        S3(**mock_invalid_s3_config)
