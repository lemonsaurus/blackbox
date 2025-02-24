"""Test the cron/rotation strategy helpers."""
from datetime import datetime
from datetime import timezone
from unittest.mock import patch

import pytest
from pytest_mock import Tuple

import blackbox.utils.rotation as rotation


SAMPLE_DATETIME_1 = datetime(2025, 2, 24, 15, 38, 45, tzinfo=timezone.utc)
SAMPLE_DATETIME_2 = datetime(2025, 1, 5, 10, 18, 36, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def mock_datetime_now():
    """Mock the value of datetime.now() so it's consistent whenever tests are run."""
    # Fix now() to: February 25th, 2025 at 12:00 UTC
    fixed_now = datetime(2025, 2, 25, 12, 0, 0, tzinfo=timezone.utc)
    with patch("blackbox.utils.rotation.datetime") as mock_datetime:
        mock_datetime.now.return_value = fixed_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)
        yield


@pytest.fixture
def mock_cron_expression_datetime_cases():
    """Mock cases for cron expressions, datetime to test, and the expected value."""
    return [
        (
            # 04:00 - 04:59
            "* 4 * * *",
            datetime(year=2025, month=2, day=21,
                     hour=4, minute=25, second=35, microsecond=1),
            True,
        ),
        (
            # :30
            "30 * * * *",
            datetime(year=2012, month=7, day=6,
                     hour=9, minute=25, second=35, microsecond=1),
            False,
        ),
        (
            # :30
            "30 * * * *",
            datetime(year=2012, month=7, day=6,
                     hour=9, minute=30, second=35, microsecond=1),
            True,
        ),
        (
            # 1st day of any month
            "* * 1 * *",
            datetime(year=2012, month=7, day=6,
                     hour=9, minute=30, second=35, microsecond=1),
            False,
        ),
        (
            # 2nd month (February)
            "* * * 2 *",
            datetime(year=2022, month=2, day=16,
                     hour=12, minute=30, second=45, microsecond=17),
            True,
        ),
        (
            # 2nd month (February)
            "* * * 2 *",
            datetime(year=2022, month=5, day=16,
                     hour=12, minute=30, second=45, microsecond=17),
            False,
        ),
        (
            # Any time on a Sunday
            "* * * * 7",
            datetime(year=2025, month=2, day=23,  # Sunday
                     hour=12, minute=30, second=45, microsecond=17),
            True,
        ),
        (
            # Any time on a Sunday
            "* * * * 7",
            datetime(year=2025, month=2, day=22,  # Saturday
                     hour=12, minute=30, second=45, microsecond=17),
            False,
        ),
        (
            # 03:12 on December 4th
            "12 3 4 12 *",
            datetime(year=2025, month=2, day=22,
                     hour=12, minute=30, second=45, microsecond=17),
            False,
        ),
        (
            # 03:12 on December 4th
            "12 3 4 12 *",
            datetime(year=2025, month=12, day=4,
                     hour=3, minute=12, second=45, microsecond=17),
            True,
        ),
        (
            # 1st or 2nd of any month at either 02:05 or 02:10 AM
            "5,10 2 1,2 * *",
            datetime(year=2025, month=12, day=4,
                     hour=3, minute=12, second=45, microsecond=17),
            False,
        ),
        (
            # 1st or 2nd of any month at either 02:05 or 02:10 AM
            "5,10 2 1,2 * *",
            datetime(year=2025, month=12, day=2,
                     hour=2, minute=5, second=45, microsecond=17),
            True,
        ),
        (
            # Any Sunday between 00:00 and 06:59
            "* 0-6 * * 0",
            datetime(year=2025, month=2, day=23,
                     hour=3, minute=12, second=45, microsecond=17),
            True,
        ),
        (
            # Any Sunday between 00:00 and 06:59
            "* 0-6 * * 0",
            datetime(year=2025, month=2, day=23,
                     hour=6, minute=12, second=45, microsecond=17),
            True,
        ),
        (
            # Any Sunday between 00:00 and 06:59
            "* 0-6 * * 0",
            datetime(year=2025, month=2, day=23,
                     hour=7, minute=0, second=45, microsecond=17),
            False,
        ),
    ]


@pytest.fixture
def mock_cron_expressions_to_clean():
    """Mock cases for cron expressions to clean."""
    return [
        ("* * * 2 * *", "* * * 2 *"),
        ("25 10 * * * *", "25 10 * * *"),
        ("* 11 * * 1 1", "* 11 * * 1"),
        ("2 4 5 7 4 0", "2 4 5 7 4"),
        ("* 3/2 1,3,4 5-9 * 5", "* 3/2 1,3,4 5-9 *")
    ]


@pytest.fixture
def mock_rotation_strategies():
    """Mock rotation strategies config."""
    return [
        "* * * 2 * *",
        "25 10 * * * *",
        "* 11 * * 1 1",
        "2 4 5 7 4 0",
        "* 3/2 1,3,4 5-9 * 5",
        "1 1 3 4 7",
        "* * * * *",
    ]


@pytest.fixture
def mock_cron_expressions():
    """Mock cron expressions against which to match a provided datetime."""
    return [
        "* * * 2 *",  # Any time in February
        "38 15 * * *",  # 15:38 UTC, any day, any month
        "* 11 * * 1",  # 11:00 - 11:59 UTC, Mondays, any month
        "26 * 4 * *",  # The 26th minute of any hour, on the 4th of any month
        "* * * * 1",  # Any time on any Monday
        "12 4 5 2 7",  # 4:12, on the 5th of February, if it's a Sunday
        "* 0/3 * * *",  # Every 3rd hour from 0-23, any minute, any day, any month
        "38 15 24 2 1",  # 15:38 UTC, on the 24th of February, if it's a Monday
        "* * 19 * 7",  # Any time on the 19th day of any month, if it's a Sunday
        "* 10-15 * 2 *",  # Any minute in any hour from 10 through 15 in February
        "* * 2,24,28 1,2,3 *",  # Any time in Jan/Feb/Mar, on the 2nd/24th/28th day
        "* * 2,28 1,2,3 *",  # Any time in Jan/Feb/Mar, on the 2nd/28th day
        "* * * * *",  # Literally any time
    ]


@pytest.fixture
def mock_retention_tracker():
    """Mock a retention tracker."""
    return {
        "* * * 2 *": {
            "num_retained": 0,
            "max": 9999999,
        },
        "25 10 * * *": {
            "num_retained": 0,
            "max": 9999999,
        },
        "* 11 * * 1": {
            "num_retained": 0,
            "max": 1,
        },
        "2 4 5 7 4": {
            "num_retained": 0,
            "max": 0,
        },
        "* 3/2 1,3,4 5-9 *": {
            "num_retained": 0,
            "max": 5,
        },
        "1 1 3 4 7": {
            "num_retained": 0,
            "max": 9999999,
        },
        "* * * * *": {
            "num_retained": 0,
            "max": 9999999,
        },
    }


@pytest.fixture
def mock_meets_delete_criteria_params():
    """Mock params for the `meets_delete_criteria` helper."""
    return [
        {
            "args": {
                "max_to_retain": 1,
                "num_retained": 1,
                "days": 5,
                "dt": SAMPLE_DATETIME_1,
            },
            "expected_response": False,
        },
        {
            "args": {
                "max_to_retain": 2,
                "num_retained": 1,
                "days": 5,
                "dt": SAMPLE_DATETIME_1,
            },
            "expected_response": False,
        },
        {
            "args": {
                "max_to_retain": 0,
                "num_retained": 2,
                "days": 7,
                "dt": SAMPLE_DATETIME_1,
            },
            "expected_response": False,
        },
        {
            "args": {
                "max_to_retain": 1,
                "num_retained": 1,
                "days": 5,
                "dt": SAMPLE_DATETIME_2,
            },
            "expected_response": True,
        },
        {
            "args": {
                "max_to_retain": 10,
                "num_retained": 1,
                "days": 5,
                "dt": SAMPLE_DATETIME_2,
            },
            "expected_response": False,
        },
    ]


@pytest.fixture
def mock_retention_days() -> list[Tuple[int | None, datetime, bool]]:
    """Mock different retention days configurations."""
    return [
        (None, SAMPLE_DATETIME_1, True),
        (0, SAMPLE_DATETIME_1, True),
        (7, SAMPLE_DATETIME_1, True),
        (20, SAMPLE_DATETIME_2, False),
        (45, SAMPLE_DATETIME_2, False),
        (55, SAMPLE_DATETIME_2, True),
        (100, SAMPLE_DATETIME_2, True),
    ]


def test_cron_datetime_matcher_works(mock_cron_expression_datetime_cases):
    """Test that the matches_cron helper accurately matches datetimes to cron
    expressions."""
    for dt in mock_cron_expression_datetime_cases:
        assert rotation.matches_cron(cron_expression=dt[0], dt=dt[1]) == dt[2]


def test_clean_cron_expression(mock_cron_expressions_to_clean):
    """Test that cron expressions are properly cleaned to retain the first 5 values."""
    for exp in mock_cron_expressions_to_clean:
        assert rotation.clean_cron_expression(exp[0]) == exp[1]


def test_batch_cron_datetime_matcher_works(mock_cron_expressions):
    """Test that the batch cron datetime matcher is accurate."""
    matches = rotation.matches_crons(
        cron_expressions=mock_cron_expressions,
        dt=SAMPLE_DATETIME_1,
    )
    assert matches == [
        "* * * 2 *",  # Any time in February
        "38 15 * * *",  # 15:38 UTC, any day, any month
        "* * * * 1",  # Any time on any Monday
        "* 0/3 * * *",  # Every 3rd hour from 0-23, any minute, any day, any month
        "38 15 24 2 1",  # 15:38 UTC, on the 24th of February, if it's a Monday
        "* 10-15 * 2 *",  # Any minute in any hour from 10 through 15 in February
        "* * 2,24,28 1,2,3 *",  # Any time in Jan/Feb/Mar, on the 2nd/24th/28th day
        "* * * * *",  # Literally any time
    ]


def test_datetime_field_matching():
    """Test that matching different fields of a datetime accurately resolve to True or
    False when matched against the corresponding part of a cron expression."""
    # Test that matching returns True when expected
    exp = "38 15 24 2 1"
    exp_parts = exp.split()
    assert rotation.match_field(SAMPLE_DATETIME_1.minute, exp_parts[0])
    assert rotation.match_field(SAMPLE_DATETIME_1.hour, exp_parts[1])
    assert rotation.match_field(SAMPLE_DATETIME_1.day, exp_parts[2])
    assert rotation.match_field(SAMPLE_DATETIME_1.month, exp_parts[3])
    assert rotation.match_field(
        SAMPLE_DATETIME_1.isoweekday(),
        exp_parts[4],
        is_weekday=True,
    )

    # Test that matching returns False when expected
    assert not rotation.match_field(SAMPLE_DATETIME_2.minute, exp_parts[0])
    assert not rotation.match_field(SAMPLE_DATETIME_2.hour, exp_parts[1])
    assert not rotation.match_field(SAMPLE_DATETIME_2.day, exp_parts[2])
    assert not rotation.match_field(SAMPLE_DATETIME_2.month, exp_parts[3])
    assert not rotation.match_field(
        SAMPLE_DATETIME_2.isoweekday(),
        exp_parts[4],
        is_weekday=True,
    )


def test_date_within_retention_days(mock_retention_days):
    """Test that `within_retention_days` correctly returns whether a provided datetime
    is within the provided number of days ago."""
    for retention_days in mock_retention_days:
        assert rotation.within_retention_days(
            days=retention_days[0],
            dt=retention_days[1],
        ) == retention_days[2]


def test_construct_retention_tracker(mock_rotation_strategies, mock_retention_tracker):
    """Test that the retention tracker matches the expected format."""
    assert rotation.construct_retention_tracker(
        cron_expressions=mock_rotation_strategies,
    ) == mock_retention_tracker


def test_correct_highest_max_retention_count(mock_retention_tracker):
    """Test that the expression with the highest max is correctly returned."""
    highest_max_exp = rotation.get_highest_max_retention_count(
        retention_tracker=mock_retention_tracker,
        cron_expressions=["* 3/2 1,3,4 5-9 *", "* 11 * * 1"],
    )
    assert highest_max_exp == ("* 3/2 1,3,4 5-9 *", 5)


def test_meets_delete_criteria(mock_meets_delete_criteria_params):
    """Test whether the `meets_delete_criteria` helper returns the expected value."""
    for params in mock_meets_delete_criteria_params:
        assert (
            rotation.meets_delete_criteria(**params["args"])
            == params["expected_response"]
        )
