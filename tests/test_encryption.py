import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from blackbox.utils.encryption import EncryptionHandler
from blackbox.utils.encryption import create_encryption_handler


class TestEncryptionHandler:
    """Test cases for the EncryptionHandler class."""

    def test_no_encryption(self):
        """Test that no encryption returns the original file."""
        config = {"method": "none"}
        handler = EncryptionHandler(config)

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test data")
            test_file = Path(f.name)

        try:
            result = handler.encrypt_file(test_file)
            assert result == test_file
        finally:
            test_file.unlink()

    def test_invalid_method_raises_error(self):
        """Test that invalid encryption method raises ValueError."""
        config = {"method": "invalid"}
        with pytest.raises(ValueError, match="Invalid encryption method"):
            EncryptionHandler(config)

    def test_password_encryption_without_password_raises_error(self):
        """Test that password encryption without password raises ValueError."""
        config = {"method": "password"}
        handler = EncryptionHandler(config)

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("test data")
            test_file = Path(f.name)

        try:
            with pytest.raises(ValueError, match="Password is required"):
                handler.encrypt_file(test_file)
        finally:
            test_file.unlink()

    @patch('subprocess.run')
    def test_password_encryption_success(self, mock_run):
        """Test successful password encryption."""
        # Mock successful gpg command
        mock_run.return_value.returncode = 0
        mock_run.return_value.stderr = ""

        config = {"method": "password", "password": "test_password"}
        handler = EncryptionHandler(config)

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql') as f:
            f.write("test data")
            test_file = Path(f.name)

        try:
            # Create the expected encrypted file
            encrypted_path = test_file.with_suffix('.sql.gpg')
            encrypted_path.write_text("encrypted content")

            result = handler.encrypt_file(test_file)

            assert result == encrypted_path
            assert encrypted_path.exists()

            # Verify gpg was called correctly
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            assert "gpg" in call_args
            assert "--symmetric" in call_args
            assert "test_password" in call_args

        finally:
            test_file.unlink()
            if encrypted_path.exists():
                encrypted_path.unlink()

    def test_cleanup_temp_file(self):
        """Test cleanup with 'none' method doesn't delete files."""
        config = {"method": "none"}
        handler = EncryptionHandler(config)

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test data")
            test_file_path = Path(f.name)

        try:
            # Verify cleanup doesn't remove the file when method is 'none'
            assert test_file_path.exists()
            handler.cleanup_temp_file(test_file_path)
            assert test_file_path.exists()  # Should still exist
        finally:
            if test_file_path.exists():
                test_file_path.unlink()


class TestCreateEncryptionHandler:
    """Test cases for the create_encryption_handler function."""

    def test_create_handler_with_config(self):
        """Test creating handler with configuration."""
        config = {"encryption": {"method": "none"}}
        handler = create_encryption_handler(config)

        assert isinstance(handler, EncryptionHandler)
        assert handler.method == "none"

    def test_create_handler_with_empty_config(self):
        """Test creating handler with empty configuration."""
        config = {}
        handler = create_encryption_handler(config)

        assert isinstance(handler, EncryptionHandler)
        assert handler.method == "none"
