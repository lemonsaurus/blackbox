import pytest

from blackbox.utils.encryption import EncryptionHandler


class TestPasswordValidation:
    """Test cases for password strength validation."""

    def test_strong_password_accepted(self):
        """Test that strong passwords are accepted."""
        strong_passwords = [
            "VerySecurePassword123",
            "MyReallyStrongPassword456",
            "ComplexPasswordWithNumbers789",
            "AnotherStrongPassword012",
            "fourteencharacter1",  # Exactly 14 chars
        ]

        for password in strong_passwords:
            config = {"method": "password", "password": password}
            handler = EncryptionHandler(config)
            # Should not raise an exception
            handler._validate_password_strength(password)

    def test_weak_password_rejected(self):
        """Test that weak passwords are rejected."""
        weak_passwords = [
            "short",  # Too short
            "thirteenchars",  # 13 chars, too short
            "onlylowercaseletters",  # No uppercase/numbers (20 chars)
            "ONLYUPPERCASELETTERS",  # No lowercase/numbers (20 chars)
            "fourteennumbers",  # No uppercase/numbers (14 chars, only lowercase)
        ]

        for password in weak_passwords:
            config = {"method": "password", "password": password}
            handler = EncryptionHandler(config)
            with pytest.raises(ValueError, match="Password must|at least 14 characters"):
                handler._validate_password_strength(password)

    def test_minimum_length_validation(self):
        """Test minimum password length validation."""
        config = {"method": "password", "password": "1234567890123"}  # 13 chars
        handler = EncryptionHandler(config)

        with pytest.raises(ValueError, match="at least 14 characters"):
            handler._validate_password_strength("1234567890123")

    def test_complexity_validation(self):
        """Test password complexity validation."""
        # 14+ chars but no complexity
        config = {"method": "password", "password": "simplepasswordonly"}
        handler = EncryptionHandler(config)

        with pytest.raises(ValueError, match="at least 2 of"):
            handler._validate_password_strength("simplepasswordonly")
