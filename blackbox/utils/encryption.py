import base64
import contextlib
import gzip
import os
import re
from pathlib import Path
from typing import Any
from typing import Dict

from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from blackbox.utils.logger import log


class EncryptionHandler:
    """
    🔒 Handles password-based encryption of backup files using Python cryptography.

    Uses Fernet symmetric encryption (AES 128 in CBC mode with HMAC) with
    PBKDF2 key derivation. Files are compressed before encryption for better
    security and smaller file sizes.

    Security Notes:
        - Passwords must be strong and kept secure
        - Lost passwords result in permanently inaccessible backups
        - Uses a fixed salt for consistency across environments
        - Temporary files are securely overwritten during cleanup
    """

    def __init__(self, encryption_config: Dict[str, Any]) -> None:
        self.config = encryption_config
        self.method = self.config.get("method", "none").lower()

        if self.method not in ["none", "password"]:
            raise ValueError(f"Invalid encryption method: {self.method}")

    def encrypt_file(self, file_path: Path) -> Path:
        """Main encryption entry point - encrypts file if method is 'password'."""
        if self.method == "none":
            return file_path
        elif self.method == "password":
            return self._encrypt_with_fernet(file_path)
        
        # This should be unreachable due to __init__ validation, but included for type safety
        raise ValueError(f"Unknown encryption method: {self.method}")

    def _encrypt_with_fernet(self, file_path: Path) -> Path:
        """Core encryption logic: compress → encrypt → save with .enc extension."""
        password = self.config.get("password")
        if not password:
            raise ValueError("Password is required for encryption")

        self._validate_password_strength(password)

        log.info(f"Encrypting {file_path.name}")

        encrypted_path = file_path.with_suffix(f"{file_path.suffix}.enc")

        try:
            key = self._derive_key(password.encode())
            fernet = Fernet(key)

            with open(file_path, 'rb') as f:
                data = f.read()

            # Compress first for smaller encrypted files and better security
            compressed_data = gzip.compress(data)
            encrypted_data = fernet.encrypt(compressed_data)

            with open(encrypted_path, 'wb') as f:
                f.write(encrypted_data)

            log.info(f"File encrypted: {encrypted_path.name}")
            return encrypted_path

        except Exception as e:
            # Cleanup partial files on any failure
            if encrypted_path.exists():
                with contextlib.suppress(OSError):
                    encrypted_path.unlink()

            # Provide specific error messages based on exception type
            if isinstance(e, (OSError, IOError, PermissionError)):
                error_msg = f"File operation failed during encryption: {e}"
            elif isinstance(e, (UnicodeDecodeError, UnicodeError)):
                error_msg = f"Password encoding error: {e}"
            elif isinstance(e, InvalidToken):
                error_msg = f"Encryption token error: {e}"
            elif isinstance(e, (MemoryError, OverflowError)):
                error_msg = f"Memory error during encryption: {e}"
            else:
                error_msg = f"Unexpected error during encryption: {e}"

            raise ValueError(error_msg) from e

    def _derive_key(self, password: bytes) -> bytes:
        """
        Derive encryption key from password using PBKDF2 with SHA256.

        ⚠️ Uses a fixed salt for consistency across environments. While this reduces
        some security benefits of salting (protection against rainbow tables), it ensures
        backups encrypted with the same password can be decrypted consistently.

        For maximum security in sensitive environments, consider implementing
        a configurable salt mechanism where the salt is stored alongside
        the encrypted backup metadata.
        """
        salt = b'blackbox_backup_salt_v1'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key

    def cleanup_temp_file(self, file_path: Path) -> None:
        """Securely delete encrypted temporary files with random data overwrite."""
        if file_path.exists() and self.method != "none":
            try:
                # Overwrite with random data for security, then delete
                file_size = file_path.stat().st_size
                with open(file_path, 'r+b') as f:
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())

                file_path.unlink()
                log.debug(f"Securely deleted: {file_path.name}")
            except Exception as e:
                log.warning(f"Failed to securely delete {file_path}: {e}")
                with contextlib.suppress(Exception):
                    file_path.unlink()

    def _validate_password_strength(self, password: str) -> None:
        """Validate password meets security requirements (14+ chars, 2 of 3 complexity types)."""
        if len(password) < 14:
            raise ValueError("Password must be at least 14 characters long")

        # Check complexity: uppercase, lowercase, numbers (no symbols required)
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))

        complexity_count = sum([has_upper, has_lower, has_digit])

        if complexity_count < 2:
            raise ValueError(
                "Password must contain at least 2 of: uppercase, lowercase, numbers"
            )


def create_encryption_handler(config: Dict[str, Any]) -> EncryptionHandler:
    """Factory function to create encryption handler from config."""
    encryption_config = config.get("encryption", {})
    return EncryptionHandler(encryption_config)
