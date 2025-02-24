"""Handler-agnostic cron and rotation strategy helper functions."""
from datetime import datetime
from typing import Tuple


def meets_delete_criteria(
    max_to_retain: int,
    num_retained: int,
    days: int,
    dt: datetime,
) -> bool:
    """
    Return whether the item associated with the given datetime is eligible for deletion.

    It is eligible for deletion if:
        The delta between now and the datetime is less than or equal to `days`.
        OR `days` is None
        AND
        The `num_retained` is less than or equal to `max_to_retain`.

    Args
        max_to_retain: The maximum number of items to retain.
        num_retained: The current number of items retained.
        days: The age in days of the oldest item to keep.
        dt: Datetime to check.
    Return
        Whether the item associated with the given datetime is eligible for deletion.
    """

    return (
        (
            not days  # No configured retention days
            or days and not within_retention_days(days=days, dt=dt)  # Window has passed
        )
        and (
            max_to_retain == 0 or num_retained >= max_to_retain  # Retained max backups
        )
    )


def matches_crons(cron_expressions: list[str], dt: datetime) -> list[str]:
    """
    Check if the given datetime matches at least one of the provided cron expressions.

    Args
        cron_expressions: A list of cron expressions, cleaned to ensure only 5 "parts".
        dt: Datetime to check.

    Return
        A list of matching cron expressions.
    """

    matches = []
    for exp in cron_expressions:
        if matches_cron(cron_expression=exp, dt=dt):
            matches.append(exp)
    return matches


def matches_cron(cron_expression: str, dt: datetime) -> bool:
    """
    Check if the given datetime matches the cron expression.

    Args
        cron_expression: A cron expression, cleaned to ensure only 5 "parts".
        dt: Datetime to check.
    Return
        True if the datetime fits within the cron expression, False otherwise.
    """

    # Get the different pieces of the datetime to match against the cron expression
    minute, hour, day, month = dt.minute, dt.hour, dt.day, dt.month
    # We need to use isoweekday here, because cron expressions use 7 for Sunday, whereas
    # Python's datetime.weekday() represents Sunday as 6
    weekday = dt.isoweekday()

    parts = cron_expression.split()
    if len(parts) != 5:
        raise ValueError(
            f"Invalid cron expression (should have 5 fields): {cron_expression}")
    cron_min, cron_hour, cron_day, cron_month, cron_weekday = parts

    # Check if each cron expression "part" matches the corresponding datetime "part"
    return (
        match_field(minute, cron_min)
        and match_field(hour, cron_hour)
        and match_field(day, cron_day)
        and match_field(month, cron_month)
        and match_field(weekday, cron_weekday, is_weekday=True)
    )


def match_field(dt_value: int, cron_value: str, is_weekday: bool = False) -> bool:
    """
    Match a cron expression field to a datetime "part" value.

    Args
        dt_value: A datetime "part" value. ex. 12 for day, 3 for hour, etc.
        cron_value: The value of the cron expression field corresponding with the
            datetime value. ex. If the datetime is 2025, 2, 23, 6, 12, 45, 17, and the
            cron expression is * * * 3 *, and the `dt_value` arg is 2, the `cron_value`
            arg should be 3.
        is_weekday: Whether the cron expression field we are evaluating is a weekday.

    Return
        Whether the provided value matches or falls within the range of the the cron
        expression field.
    """

    # For weekday, allow both 0 and 7 to represent Sunday
    if is_weekday and cron_value == "0":
        cron_value = "7"

    # Wildcard matches any value
    if cron_value == "*":
        return True

    # Comma-separated list, ex. "1,5,10"
    if "," in cron_value:
        options = []
        for part in cron_value.split(","):
            part = part.strip()
            if is_weekday and part == "0":
                options.append(7)
            else:
                options.append(int(part))
        return dt_value in options

    # Ranges, ex. "1-5"
    if "-" in cron_value:
        start_str, end_str = cron_value.split("-")
        start = int(start_str) if not (is_weekday and start_str == "0") else 7
        end = int(end_str) if not (is_weekday and end_str == "0") else 7
        return start <= dt_value <= end

    # Step values, ex. "*/15" or "5/10"
    if "/" in cron_value:
        base, step_str = cron_value.split("/")
        step = int(step_str)
        if base == "*":
            return dt_value % step == 0
        else:
            base_val = int(base)
            return (dt_value - base_val) % step == 0

    # Direct number match
    try:
        return dt_value == int(cron_value)
    except ValueError:
        raise ValueError(f"Cannot parse cron value: {cron_value}")


def within_retention_days(days: int, dt: datetime) -> bool:
    """Return whether the provided datetime is between now and `days` days ago."""
    if not days:
        return True
    now = datetime.now(tz=dt.tzinfo)
    delta = now - dt
    return delta.days <= days


def construct_retention_tracker(
    cron_expressions: list[str],
) -> dict[str, dict[str, int]]:
    """Construct a dictionary tracking how many retentions have occurred for a file
    matching each cron expression."""
    unlimited = 9999999  # Who's going to have 9999999 backups? Probably no-one.
    tracker = {}
    if not cron_expressions:
        return tracker  # No expressions configured
    for exp in cron_expressions:
        exp = exp.split()
        if len(exp) == 6:
            num_to_retain = exp.pop()
            try:
                num_to_retain = int(num_to_retain)
            except ValueError:
                # This will happen if the num to retain config is not an integer, ex. if
                # its value is "*" (the wild card). If the value is something silly,
                # retain unlimited backups, to err on the side of caution.
                num_to_retain = unlimited
        else:
            # The user did not include a 6th value, so assume unlimited
            num_to_retain = unlimited
        exp = " ".join(exp)
        tracker[exp] = {
            "num_retained": 0,
            "max": num_to_retain,
        }
    return tracker


def get_highest_max_retention_count(
    retention_tracker: dict[str, dict[str, int]],
    cron_expressions: list[str],
) -> Tuple[str, int]:
    """
    Get the highest maximum retention count.

    Return
        The highest maximum retention count configured between the provided cron
        expressions, or 0 if the expression is not in the tracker.
    """

    maximum = 0
    highest_exp = ""
    for exp in cron_expressions:
        if exp in retention_tracker and retention_tracker[exp]["max"] > maximum:
            maximum = retention_tracker[exp]["max"]
            highest_exp = exp
    return (highest_exp, maximum)


def clean_cron_expression(cron_expression: list[str]) -> str:
    """
    Clean a potentially bastardized cron expression.

    Remove the sixth option, if it exists. Otherwise, just return the expression as-is.

    Sample input: "* * 4 * * 7"
    Sample output: "* * 4 * *"
    """

    parts = cron_expression.split()
    if len(parts) == 6:
        parts.pop()
    return " ".join(parts).strip()
