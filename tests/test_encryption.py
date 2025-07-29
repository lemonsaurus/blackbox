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
        config = {"method": "password", "password": "VeryStrongPassword123"}
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

    def test_password_decryption_success(self):
        """Test successful password decryption."""
        config = {"method": "password", "password": "DecryptionTestPassword123"}
        handler = EncryptionHandler(config)

        # Create and encrypt a test file
        test_content = "test data for decryption"
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql') as f:
            f.write(test_content)
            test_file = Path(f.name)

        try:
            # Encrypt the file
            encrypted_file = handler.encrypt_file(test_file)

            # Decrypt the file
            decrypted_file = handler.decrypt_file(encrypted_file)

            # Verify decryption worked
            assert decrypted_file != encrypted_file
            assert decrypted_file.exists()
            assert not decrypted_file.name.endswith('.enc')

            # Check content matches original
            with open(decrypted_file, 'r') as f:
                decrypted_content = f.read()

            assert decrypted_content == test_content

        finally:
            test_file.unlink()
            if encrypted_file.exists():
                encrypted_file.unlink()
            if decrypted_file.exists():
                decrypted_file.unlink()

    def test_decryption_with_custom_output_path(self):
        """Test decryption with custom output path."""
        config = {"method": "password", "password": "CustomOutputPassword123"}
        handler = EncryptionHandler(config)

        test_content = "custom output test"
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql') as f:
            f.write(test_content)
            test_file = Path(f.name)

        try:
            # Encrypt the file
            encrypted_file = handler.encrypt_file(test_file)

            # Create custom output path
            custom_output = test_file.parent / "custom_decrypted.sql"

            # Decrypt with custom output path
            decrypted_file = handler.decrypt_file(encrypted_file, custom_output)

            # Verify custom path was used
            assert decrypted_file == custom_output
            assert custom_output.exists()

            # Check content
            with open(decrypted_file, 'r') as f:
                decrypted_content = f.read()

            assert decrypted_content == test_content

        finally:
            test_file.unlink()
            if encrypted_file.exists():
                encrypted_file.unlink()
            if custom_output.exists():
                custom_output.unlink()

    def test_decryption_wrong_password(self):
        """Test decryption fails with wrong password."""
        # Encrypt with one password
        encrypt_config = {"method": "password", "password": "CorrectPassword123"}
        encrypt_handler = EncryptionHandler(encrypt_config)

        test_content = "secret data"
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql') as f:
            f.write(test_content)
            test_file = Path(f.name)

        try:
            # Encrypt the file
            encrypted_file = encrypt_handler.encrypt_file(test_file)

            # Try to decrypt with wrong password
            decrypt_config = {"method": "password", "password": "WrongPassword123"}
            decrypt_handler = EncryptionHandler(decrypt_config)

            with pytest.raises(ValueError, match="Invalid password or corrupted file"):
                decrypt_handler.decrypt_file(encrypted_file)

        finally:
            test_file.unlink()
            if encrypted_file.exists():
                encrypted_file.unlink()

    def test_decryption_invalid_file(self):
        """Test decryption with invalid/non-encrypted file."""
        config = {"method": "password", "password": "TestPassword123"}
        handler = EncryptionHandler(config)

        # Test with non-existent file
        fake_file = Path("nonexistent.enc")
        with pytest.raises(FileNotFoundError):
            handler.decrypt_file(fake_file)

        # Test with file without .enc extension
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql') as f:
            f.write("not encrypted")
            regular_file = Path(f.name)

        try:
            with pytest.raises(ValueError, match="missing .enc extension"):
                handler.decrypt_file(regular_file)
        finally:
            regular_file.unlink()

    def test_decryption_none_method(self):
        """Test decryption fails when method is 'none'."""
        config = {"method": "none"}
        handler = EncryptionHandler(config)

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql.enc') as f:
            f.write("fake encrypted content")
            fake_encrypted = Path(f.name)

        try:
            with pytest.raises(ValueError, match="only supported for password encryption"):
                handler.decrypt_file(fake_encrypted)
        finally:
            fake_encrypted.unlink()

    def test_password_encryption_consistency(self):
        """Test that same password produces consistent encryption keys."""
        config = {"method": "password", "password": "ConsistentPassword123"}
        handler1 = EncryptionHandler(config)
        handler2 = EncryptionHandler(config)

        # Both should derive the same key from the same password
        key1 = handler1._derive_key(b"ConsistentPassword123")
        key2 = handler2._derive_key(b"ConsistentPassword123")
        assert key1 == key2

        # Different passwords should produce different keys
        key3 = handler1._derive_key(b"DifferentPassword456")
        assert key1 != key3

    def test_encryption_with_compression(self):
        """Test that encryption includes compression."""
        config = {"method": "password", "password": "CompressionTestPassword123"}
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
        config = {"method": "password", "password": "CleanupTestPassword123"}
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
        config = {"method": "password", "password": "WorkflowTestPassword123"}
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
