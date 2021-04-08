import pytest

from blackbox.exceptions import MissingFields
from blackbox.handlers.storage import Dropbox


@pytest.fixture
def mock_valid_dropbox_config():
    """Mock valid Dropbox config."""
    return {"access_token": "XXXXXXX", "upload_directory": "/home/dropbox_user/Documents/"}


@pytest.fixture
def mock_invalid_dropbox_config():
    """Mock invalid Dropbox config."""
    return {}


def test_dropbox_handler_can_be_instantiated_with_required_fields(mock_valid_dropbox_config):
    """Test if the dropbox storage handler can be instantiated."""
    Dropbox(**mock_valid_dropbox_config)


def test_dropbox_handler_fails_without_required_fields(mock_invalid_dropbox_config):
    """Test if the dropbox storage handler cannot be instantiated with missing fields."""
    with pytest.raises(MissingFields):
        Dropbox(**mock_invalid_dropbox_config)


def test_dropbox_handler_instantiates_optional_fields(mock_valid_dropbox_config):
    """Test if the dropbox storage handler instantiates optional fields."""
    dropbox_instance = Dropbox(**mock_valid_dropbox_config)
    assert dropbox_instance.upload_base == "/home/dropbox_user/Documents/"
