import tempfile
from pathlib import Path

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

    def test_password_encryption_success(self):
        """Test successful password encryption."""
        config = {"method": "password", "password": "test_password"}
        handler = EncryptionHandler(config)

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql') as f:
            f.write("test data for encryption")
            test_file = Path(f.name)

        try:
            encrypted_file = handler.encrypt_file(test_file)

            # Should create a new file with .enc extension
            assert encrypted_file != test_file
            assert encrypted_file.exists()
            assert encrypted_file.suffix == '.enc'
            assert encrypted_file.name.endswith('.sql.enc')

            # Original file should still exist
            assert test_file.exists()

            # Encrypted file should have different content and be binary
            with open(encrypted_file, 'rb') as f:
                encrypted_content = f.read()

            with open(test_file, 'r') as f:
                original_content = f.read()

            # Encrypted content should be different and binary
            assert len(encrypted_content) > 0
            assert encrypted_content != original_content.encode()

        finally:
            test_file.unlink()
            if encrypted_file.exists():
                encrypted_file.unlink()

    def test_password_encryption_consistency(self):
        """Test that same password produces consistent encryption keys."""
        config = {"method": "password", "password": "consistent_password"}
        handler1 = EncryptionHandler(config)
        handler2 = EncryptionHandler(config)

        # Both should derive the same key from the same password
        key1 = handler1._derive_key(b"consistent_password")
        key2 = handler2._derive_key(b"consistent_password")
        assert key1 == key2

        # Different passwords should produce different keys
        key3 = handler1._derive_key(b"different_password")
        assert key1 != key3

    def test_encryption_with_compression(self):
        """Test that encryption includes compression."""
        config = {"method": "password", "password": "test_password"}
        handler = EncryptionHandler(config)

        # Create a file with repetitive content that compresses well
        test_content = "This is repetitive content. " * 100
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write(test_content)
            test_file = Path(f.name)

        try:
            encrypted_file = handler.encrypt_file(test_file)

            # Encrypted file should exist
            assert encrypted_file.exists()

            # Due to compression + encryption, size relationship may vary
            # but encrypted file should be binary data
            with open(encrypted_file, 'rb') as f:
                encrypted_data = f.read()

            assert len(encrypted_data) > 0
            # Fernet adds authentication and timestamp, so it's always longer than minimum

        finally:
            test_file.unlink()
            if encrypted_file.exists():
                encrypted_file.unlink()

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

    def test_cleanup_encrypted_file(self):
        """Test cleanup removes encrypted files when method is 'password'."""
        config = {"method": "password", "password": "test_password"}
        handler = EncryptionHandler(config)

        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"test data")
            test_file_path = Path(f.name)

        try:
            assert test_file_path.exists()
            handler.cleanup_temp_file(test_file_path)
            assert not test_file_path.exists()  # Should be deleted
        finally:
            # Cleanup in case test fails
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

    def test_encryption_with_compression_workflow(self):
        """Test that encryption works correctly in compression workflow."""
        config = {"method": "password", "password": "test_password"}
        handler = EncryptionHandler(config)

        # Create a test file that would be compressed
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql') as f:
            f.write("test data for compression and encryption")
            test_file = Path(f.name)

        try:
            # Simulate compressed temp file (what S3 handler would create)
            compressed_file = test_file.with_suffix('.gz')
            compressed_file.write_bytes(b"compressed data")

            result = handler.encrypt_file(compressed_file)

            # Should create encrypted file with .enc extension
            expected_path = Path(str(compressed_file) + '.enc')
            assert result == expected_path
            assert expected_path.exists()

            # Verify the compressed file was encrypted, not the original
            assert result.name.endswith('.gz.enc')

        finally:
            test_file.unlink()
            if compressed_file.exists():
                compressed_file.unlink()
            if result.exists():
                result.unlink()
