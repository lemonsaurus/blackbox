import base64
import gzip
import os
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from blackbox.utils.logger import log


class EncryptionHandler:
    """Handles basic password-based encryption of backup files using Python cryptography."""

    def __init__(self, encryption_config: dict):
        """Initialize encryption handler with configuration."""
        self.config = encryption_config
        self.method = self.config.get("method", "none").lower()

        if self.method not in ["none", "password"]:
            raise ValueError(f"Invalid encryption method: {self.method}")

    def encrypt_file(self, file_path: Path) -> Path:
        """Encrypt a file if password encryption is enabled."""
        if self.method == "none":
            return file_path
        elif self.method == "password":
            return self._encrypt_with_fernet(file_path)

    def _encrypt_with_fernet(self, file_path: Path) -> Path:
        """Encrypt file using Fernet symmetric encryption."""
        password = self.config.get("password")
        if not password:
            raise ValueError("Password is required for encryption")

        log.info(f"Encrypting {file_path.name}")

        # Create encrypted file path
        encrypted_path = file_path.with_suffix(f"{file_path.suffix}.enc")

        try:
            # Generate key from password
            key = self._derive_key(password.encode())
            fernet = Fernet(key)

            # Read and encrypt file
            with open(file_path, 'rb') as f:
                data = f.read()

            # Compress then encrypt
            compressed_data = gzip.compress(data)
            encrypted_data = fernet.encrypt(compressed_data)

            # Write encrypted data to file
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted_data)

            log.info(f"File encrypted: {encrypted_path.name}")
            return encrypted_path

        except Exception as e:
            if encrypted_path.exists():
                encrypted_path.unlink()
            raise ValueError(f"Encryption failed: {e}")

    def _derive_key(self, password: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        # Use a fixed salt for simplicity (in production, should be random and stored)
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
        """Securely delete a temporary file."""
        if file_path.exists() and self.method != "none":
            try:
                # Overwrite with random data then delete
                file_size = file_path.stat().st_size
                with open(file_path, 'r+b') as f:
                    f.write(os.urandom(file_size))
                    f.flush()
                    os.fsync(f.fileno())

                file_path.unlink()
                log.debug(f"Securely deleted: {file_path.name}")
            except Exception as e:
                log.warning(f"Failed to securely delete {file_path}: {e}")
                try:
                    file_path.unlink()
                except Exception:
                    pass


def create_encryption_handler(config: dict) -> EncryptionHandler:
    """Create an encryption handler based on configuration."""
    encryption_config = config.get("encryption", {})
    return EncryptionHandler(encryption_config)
