from unittest.mock import patch
import pytest

from blackbox.exceptions import MissingFields
from blackbox.handlers.storage import GoogleDrive


@pytest.fixture
def mock_valid_google_drive_config():
    """Mock valid Google Drive config."""
    return {
        "refresh_token": "XXXXXXX",
        "client_id": "XXXXXXX",
        "client_secret": "XXXXXXX",
        "upload_directory": "Blackbox",
    }


@pytest.fixture
def mock_invalid_google_drive_config():
    """Mock invalid Google Drive config."""
    return {}


@patch("blackbox.handlers.storage.GoogleDrive._initialize_drive_client")
def test_google_drive_handler_can_be_instantiated_with_required_fields(
        mock_initialize_drive_client, mock_valid_google_drive_config):
    """Test if the Google Drive storage handler can be instantiated."""
    GoogleDrive(**mock_valid_google_drive_config)
    mock_initialize_drive_client.assert_called_once()


@patch("blackbox.handlers.storage.GoogleDrive._initialize_drive_client")
def test_google_drive_handler_fails_without_required_fields(
        mock_initialize_drive_client, mock_invalid_google_drive_config):
    """Test if the Google Drive storage handler cannot be instantiated with missing
    fields."""
    with pytest.raises(MissingFields):
        GoogleDrive(**mock_invalid_google_drive_config)
    mock_initialize_drive_client.assert_not_called()


@patch("blackbox.handlers.storage.GoogleDrive._initialize_drive_client")
def test_google_drive_handler_instantiates_optional_fields(
        mock_initialize_drive_client, mock_valid_google_drive_config):
    """Test if the Google Drive storage handler instantiates optional fields."""
    google_drive_instance = GoogleDrive(**mock_valid_google_drive_config)
    assert google_drive_instance.upload_base == "Blackbox"
    mock_initialize_drive_client.assert_called_once()

def test_google_drive_handler_cleans_and_formats_upload_directory():
    """Test if the dropbox storage handler instantiates optional fields."""
    directories = [
        ("Blackbox", "Blackbox"),
        ("/Blackbox", "Blackbox"),
        ("/Blackbox//", "Blackbox"),
        ("////Foo/Bar", "Foo/Bar"),
        ("/Foo//Bar///Baz", "Foo/Bar/Baz"),
        ("Hello/World/////", "Hello/World"),
    ]
    for directory in directories:
        assert GoogleDrive.clean_upload_directory(directory[0]) == directory[1]
