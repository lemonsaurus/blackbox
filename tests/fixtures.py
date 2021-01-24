from textwrap import dedent

import pytest

@pytest.fixture
def config_file(mocker):
    """ Mock reading config values"""

    config = dedent("""
        databases:
            - mongodb://username:password@host:port
            - postgres://username:password@host:port

        storage:
            - s3://username:password?fire=ice&magic=blue

        notifiers:
            - https://web.hook/

        retention_days: 7
    """
    )
    mocker.patch('builtins.open', mocker.mock_open(read_data=config))
