# This is a special pytest file
import os
from textwrap import dedent

import pytest


@pytest.fixture
def config_file(mocker):
    """ Mock reading config values"""

    config = dedent(
        """
        databases:
            - mongodb://{{ MONGO_USER }}:{{ MONGO_PW }}@host:port
            - postgres://username:password@host:port

        storage:
            - s3://username:password?fire=ice&magic=blue

        notifiers:
            - https://web.hook/

        retention_days: 7
        """
    )

    os.environ["MONGO_USER"] = "mongouser"
    os.environ["MONGO_PW"] = "mongopassword"

    mocker.patch("builtins.open", mocker.mock_open(read_data=config))


@pytest.fixture
def config_file_with_errors(mocker):
    """ Mock reading config values"""

    config_with_missing_bracket = dedent(
        """
        databases:
            - mongodb://{{ MONGO_USER} :mongopassword@host:port
        """
    )

    os.environ["MONGO_USER"] = "mongouser"

    mocker.patch("builtins.open", mocker.mock_open(read_data=config_with_missing_bracket))


@pytest.fixture
def config_file_with_missing_value(mocker):
    """ Mock reading config values"""

    config_with_missing_bracket = dedent(
        """
        databases:
            - mongodb://{{ MONGO_USER }} :mongopassword@host:port
        """
    )

    # Ensure the value is unset to cause expected error
    if os.environ.get("MONGO_USER"):
        del os.environ["MONGO_USER"]

    mocker.patch("builtins.open", mocker.mock_open(read_data=config_with_missing_bracket))
