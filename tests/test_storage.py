import pytest

from blackbox.exceptions import ImproperlyConfigured
from blackbox.handlers.storage import S3


def test_s3_handler_can_be_instantiated(config_file):
    """Test if the s3 storage handler can be instantiated."""

    with pytest.raises(ImproperlyConfigured):
        S3()
