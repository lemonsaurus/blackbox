import os
from pathlib import Path

from blackbox.utils.logger import log


class EncryptionHandler:
    """Handles basic password-based encryption of backup files."""

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
            return self._encrypt_with_gpg(file_path)

    def _encrypt_with_gpg(self, file_path: Path) -> Path:
        """Encrypt file using GPG symmetric encryption."""
        password = self.config.get("password")
        if not password:
            raise ValueError("Password is required for encryption")

        log.info(f"Encrypting {file_path.name}")

        # Create encrypted file path
        encrypted_path = file_path.with_suffix(f"{file_path.suffix}.gpg")

        try:
            # Use gpg command for encryption with secure password handling
            cmd = [
                "gpg", "--batch", "--yes", "--quiet",
                "--cipher-algo", "AES256",
                "--compress-algo", "2",
                "--symmetric",
                "--passphrase-fd", "0",  # Read password from stdin
                "--output", str(encrypted_path),
                str(file_path)
            ]

            import subprocess
            result = subprocess.run(cmd, input=password, text=True, capture_output=True)

            if result.returncode != 0:
                raise RuntimeError(f"GPG encryption failed: {result.stderr}")

            log.info(f"File encrypted: {encrypted_path.name}")
            return encrypted_path

        except Exception as e:
            if encrypted_path.exists():
                encrypted_path.unlink()
            raise ValueError(f"Encryption failed: {e}")

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
