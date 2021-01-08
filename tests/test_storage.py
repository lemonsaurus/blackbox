import unittest

from blackbox.handlers import GoogleDrive


class BlackBoxStorageTests(unittest.TestCase):

    @staticmethod
    def test_gdrive_handler_can_be_instantiated():
        """Test if the GoogleDrive storage handler can be instantiated."""
        GoogleDrive()
