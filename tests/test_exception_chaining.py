import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from cryptography.fernet import InvalidToken

from blackbox.utils.encryption import EncryptionHandler


class TestExceptionChaining:
    """Test that exception chaining preserves original tracebacks."""

    def test_file_operation_error_chaining(self):
        """Test that file operation errors preserve original traceback."""
        config = {"method": "password", "password": "VeryStrongPassword123"}
        handler = EncryptionHandler(config)

        # Create a file that we'll simulate failing to read
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql') as f:
            f.write("test data")
            test_file = Path(f.name)

        try:
            # Mock open to raise a PermissionError
            with patch('builtins.open', side_effect=PermissionError("Mock permission error")):
                with pytest.raises(ValueError) as exc_info:
                    handler.encrypt_file(test_file)

                # Verify that the original exception is chained
                assert exc_info.value.__cause__ is not None
                assert isinstance(exc_info.value.__cause__, PermissionError)
                assert "Mock permission error" in str(exc_info.value.__cause__)
                assert "File operation failed during encryption" in str(exc_info.value)

        finally:
            test_file.unlink()

    def test_unknown_encryption_method_raises(self):
        """Test that unknown encryption methods raise an error."""
        # Create handler with invalid method (bypassing constructor validation)
        handler = EncryptionHandler({"method": "none"})
        handler.method = "invalid_method"  # Force invalid method

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql') as f:
            f.write("test data")
            test_file = Path(f.name)

        try:
            with pytest.raises(ValueError, match="Unknown encryption method: invalid_method"):
                handler.encrypt_file(test_file)
        finally:
            test_file.unlink()

    def test_consolidated_exception_handling_preserves_specificity(self):
        """Test that consolidated exception handler provides specific error messages."""
        config = {"method": "password", "password": "VeryStrongPassword123"}
        handler = EncryptionHandler(config)

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql') as f:
            f.write("test data")
            test_file = Path(f.name)

        try:
            # Test different exception types still get specific messages
            test_cases = [
                (PermissionError("Mock permission error"),
                 "File operation failed during encryption"),
                (UnicodeDecodeError("utf-8", b"", 0, 1, "Mock unicode error"),
                 "Password encoding error"),
                (InvalidToken("Mock token error"), "Encryption token error"),
                (MemoryError("Mock memory error"), "Memory error during encryption"),
                (RuntimeError("Mock runtime error"), "Unexpected error during encryption"),
            ]

            for exception, expected_msg in test_cases:
                with patch('builtins.open', side_effect=exception):
                    with pytest.raises(ValueError) as exc_info:
                        handler.encrypt_file(test_file)

                    # Verify specific error message
                    assert expected_msg in str(exc_info.value)
                    # Verify exception chaining is preserved
                    assert exc_info.value.__cause__ is exception

        finally:
            test_file.unlink()
