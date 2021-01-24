import unittest

from blackbox.handlers.storage import S3


class BlackBoxStorageTests(unittest.TestCase):

    @staticmethod
    def test_s3_handler_can_be_instantiated():
        """Test if the GoogleDrive storage handler can be instantiated."""
        S3()
