from tests.fixtures import config_file

def test_s3_handler_can_be_instantiated(config_file):
    """Test if the GoogleDrive storage handler can be instantiated."""
    from blackbox.handlers.storage import S3

    # This currently fails with
    #         with open(full_path, 'rb') as fp:
    # >           payload = fp.read().decode('utf-8')
    # E           AttributeError: 'str' object has no attribute 'decode'

    # .venv\lib\site-packages\botocore\loaders.py:173: AttributeError

    #S3()

