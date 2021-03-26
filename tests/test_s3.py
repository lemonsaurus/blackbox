from pathlib import Path

import pytest

from blackbox.exceptions import MissingFields
from blackbox.handlers.storage import S3


@pytest.fixture
def mock_valid_s3_config_without_aws_credentials():
    return {"bucket": "bigbucket", "endpoint": "s3.endpoint.com"}


def test_s3_handler_can_be_instantiated_with_required_fields():
    """Test if the s3 storage handler can be instantiated."""
    valid_config = {
        "bucket": "bigbucket", "endpoint": "s3.endpoint.com",
        "aws_access_key_id": "lemon", "aws_secret_access_key": "dance"
    }
    S3(**valid_config)


def test_s3_handler_can_be_instantiated_with_env_variables(
        monkeypatch, mock_valid_s3_config_without_aws_credentials
):
    """Test if the s3 storage handler can be instantiated with key & secret from env variables."""
    # Add them to the environment
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "lemon")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "dance")

    S3(**mock_valid_s3_config_without_aws_credentials)


def test_s3_handler_can_be_instantiated_with_aws_config_files(
        monkeypatch, tmp_path, mock_valid_s3_config_without_aws_credentials
):
    """Test if the s3 storage handler can be instantiated with key & secret from .aws/ files."""
    # Make valid config files
    aws_folder = tmp_path / ".aws"
    aws_folder.mkdir()
    aws_folder.joinpath("config").touch()
    aws_folder.joinpath("credentials").touch()

    # Patch pathlib.Path.home() to the temporary directory
    with monkeypatch.context() as m:
        m.setattr(Path, "home", lambda: tmp_path)
        S3(**mock_valid_s3_config_without_aws_credentials)


def test_s3_handler_fails_without_required_fields():
    """Test if the s3 storage handler cannot be instantiated with missing fields."""
    incomplete_config = {"bucket": "smolbucket"}

    with pytest.raises(MissingFields):
        S3(**incomplete_config)
