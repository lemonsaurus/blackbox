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

    environment_variables = {
        "MONGO_USER": "mongouser",
        "MONGO_PW": "mongopassword"
    }

    mocker.patch.dict(os.environ, environment_variables)

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

    environment_variables = {
        "MONGO_USER": "mongouser",
    }

    mocker.patch.dict(os.environ, environment_variables)

    mocker.patch("builtins.open", mocker.mock_open(read_data=config_with_missing_bracket))


@pytest.fixture
def config_file_with_missing_value(mocker):
    """ Mock reading config values"""

    missing_value = dedent(
        """
        databases:
            - mongodb://{{ MONGO_USER }} :mongopassword@host:port
        """
    )

    mocker.patch("builtins.open", mocker.mock_open(read_data=missing_value))
