"""Test filename format configuration functionality."""
from unittest.mock import patch

from blackbox.config import Blackbox


class TestFilenameFormat:
    """Test configurable filename format functionality."""

    def test_default_filename_format(self):
        """Test that default filename format is used when not configured."""
        # Mock the config to not have filename_format
        with patch.object(Blackbox, '_config', {'filename_format': None}):
            assert Blackbox.get_filename_format() == "{database_id}_blackbox_{date}"

    def test_custom_filename_format(self):
        """Test that custom filename format is used when configured."""
        # Mock the config to have custom filename_format
        with patch.object(Blackbox, '_config', {'filename_format': "backup_{database_id}_{date}"}):
            assert Blackbox.get_filename_format() == "backup_{database_id}_{date}"

    def test_default_date_format(self):
        """Test that default date format is used when not configured."""
        # Mock the config to not have date_format
        with patch.object(Blackbox, '_config', {'date_format': None}):
            assert Blackbox.get_date_format() == "%d_%m_%Y"

    def test_custom_date_format(self):
        """Test that custom date format is used when configured."""
        # Mock the config to have custom date_format
        with patch.object(Blackbox, '_config', {'date_format': "%Y-%m-%d"}):
            assert Blackbox.get_date_format() == "%Y-%m-%d"

    def test_rotation_patterns_default_format(self):
        """Test rotation patterns for default filename format."""
        # Mock the config to use default filename_format
        with patch.object(Blackbox, '_config', {'filename_format': None}):
            patterns = Blackbox.get_rotation_patterns("test_db")
            expected = [r"test_db_blackbox_\d{2}_\d{2}_\d{4}.+"]
            assert patterns == expected

    def test_rotation_patterns_custom_format(self):
        """Test rotation patterns for custom filename format."""
        # Mock the config to have custom filename_format
        with patch.object(Blackbox, '_config', {'filename_format': "backup_{database_id}_{date}"}):
            patterns = Blackbox.get_rotation_patterns("test_db")
            expected = [
                r"backup_test_db_\d{2}_\d{2}_\d{4}.+",
                r"test_db_blackbox_\d{2}_\d{2}_\d{4}.+"  # Legacy pattern
            ]
            assert patterns == expected

    def test_rotation_patterns_same_as_legacy(self):
        """Test that legacy pattern is not duplicated when same as current."""
        # Mock the config to have same as legacy filename_format
        config = {'filename_format': "{database_id}_blackbox_{date}"}
        with patch.object(Blackbox, '_config', config):
            patterns = Blackbox.get_rotation_patterns("test_db")
            expected = [r"test_db_blackbox_\d{2}_\d{2}_\d{4}.+"]
            assert patterns == expected
