import pytest
import requests_mock

from blackbox.exceptions import MissingFields
from blackbox.handlers.notifiers.json import Json
from blackbox.utils import reports


URL = "https://some-domain.com/api/blackbox-notifications"


@pytest.fixture
def mock_valid_json_config():
    """Mock valid Json config."""
    return {"url": URL}


@pytest.fixture
def mock_invalid_json_config():
    """Mock invalid Json config."""
    return {"key": "value"}


def test_json_handler_can_be_instantiated_with_required_fields(mock_valid_json_config):
    Json(**mock_valid_json_config)


def test_json_handler_fails_without_required_fields(mock_invalid_json_config):
    """Test if the json notifier handler cannot be instantiated with missing fields."""
    with pytest.raises(MissingFields):
        Json(**mock_invalid_json_config)


def test_json_notifier(mock_valid_json_config, report):
    """Test report parsing for raw JSON notifications."""
    json_notifier = Json(**mock_valid_json_config)
    json_notifier.report = report

    expected_report = {
        "backup-data": [
            {
                "source": "main_mongo",
                "output": "salad",
                "backup": [
                    {
                        "name": "main_s3",
                        "success": True
                    }
                ],
                "success": True
            },
            {
                "source": "secondary_mongo",
                "output": "ham-sandwich",
                "backup": [
                    {
                        "name": "main_dropbox",
                        "success": True
                    },
                    {
                        "name": "secondary_s3",
                        "success": False
                    }
                ],
                "success": False
            }
        ]
    }

    database = reports.DatabaseReport(database_id="secondary_mongo", success=False, output='')
    database.report_storage("main_dropbox", True, "ham-")
    database.report_storage("secondary_s3", False, "sandwich")

    report.databases.append(database)

    with requests_mock.Mocker() as m:
        adapter = m.post(URL)
        json_notifier.notify()
        assert adapter.call_count == 1
        assert adapter.last_request.json() == expected_report
