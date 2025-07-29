# This is a special pytest file
import os
from textwrap import dedent

import pytest

from blackbox.utils import reports


########################
# Config file Fixtures #
########################


@pytest.fixture
def config_file(mocker):
    """Mock reading config values."""
    config = dedent(
        """
        databases:
            mongodb:
                main_mongo:
                    connection_string: mongodb://{{ MONGO_USER }}:{{ MONGO_PW }}@host:port
            postgres:
                main_postgres:
                    username: username
                    password: password
                    host: host
                    port: "port"
            redis:
                main_redis:
                    password: password
                    host: host
                    port: "port"

        storage:
            s3:
                main_s3:
                    bucket: bucket
                    endpoint: s3.eu-west-1.amazonaws.com
                    aws_access_key_id: lemon
                    aws_secret_access_key: citrus
                    client_config:
                        request_checksum_calculation: when_required
                        response_checksum_validation: when_required

        notifiers:
            discord:
                test_server:
                    webhook: https://discord.com/api/webhooks/XXXX/XXXX

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
    """Mock reading config values."""
    config_with_missing_bracket = dedent(
        """
        databases:
            mongodb:
                main_mongo:
                    connection_string: mongodb://{{ MONGO_USER }:mongopassword@host:port
        """
    )

    environment_variables = {
        "MONGO_USER": "mongouser",
    }

    mocker.patch.dict(os.environ, environment_variables)

    mocker.patch("builtins.open", mocker.mock_open(read_data=config_with_missing_bracket))


@pytest.fixture
def config_file_with_missing_value(mocker):
    """Mock reading config values."""
    missing_value = dedent(
        """
        databases:
            mongodb:
                main_mongo:
                    connection_string: mongodb://{{ MONGO_USER }} :mongopassword@host:port
        """
    )

    mocker.patch("builtins.open", mocker.mock_open(read_data=missing_value))


#########################
# Notification fixtures #
#########################


@pytest.fixture
def report():
    """Notification fixture for passing in report."""
    storage = reports.StorageReport(storage_id="main_s3", success=True)

    database = reports.DatabaseReport(database_id="main_mongo", success=True, output="salad")
    database.storages = [storage]

    report = reports.Report()
    report.databases = [database]

    return report
