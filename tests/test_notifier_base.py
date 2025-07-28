"""Tests for the base BlackboxNotifier class optimization logic."""

from blackbox.handlers.notifiers._base import BlackboxNotifier
from blackbox.utils.reports import DatabaseReport
from blackbox.utils.reports import Report


class TestNotifier(BlackboxNotifier):
    """Test notifier implementation for testing base class functionality."""

    required_fields = ()
    max_output_chars = 100  # Small limit for testing

    def _parse_report(self):
        """Dummy implementation."""
        return {}

    def notify(self):
        """Dummy implementation."""
        pass


def test_output_optimization_single_failure():
    """Test output optimization for a single failed database."""
    notifier = TestNotifier()

    # Create a failed database with long output
    long_output = "Error line " + "x" * 200  # Much longer than 100
    failed_db = DatabaseReport("failed_db", False, long_output)

    report = Report()
    report.databases = [failed_db]
    notifier.report = report

    optimized_output = notifier.get_optimized_output()

    # Should be truncated to last 100 characters
    assert len(optimized_output) <= 100
    assert optimized_output.endswith("x" * 90)  # Should be tail of the output


def test_output_optimization_multiple_failures():
    """Test output optimization for multiple failed databases."""
    notifier = TestNotifier()

    # Create multiple failed databases with different output lengths
    db1 = DatabaseReport("db1", False, "Short error")
    db2 = DatabaseReport("db2", False, "Medium " + "x" * 20)
    db3 = DatabaseReport("db3", False, "Very long error " + "y" * 100)

    report = Report()
    report.databases = [db1, db2, db3]
    notifier.report = report

    optimized_output = notifier.get_optimized_output()

    # Should be within 100 character limit
    assert len(optimized_output) <= 100
    # Should contain all database IDs
    assert "db1:" in optimized_output
    assert "db2:" in optimized_output
    assert "db3:" in optimized_output


def test_output_optimization_no_failures():
    """Test output optimization when no databases failed."""
    notifier = TestNotifier()

    # Create successful databases only
    success_db = DatabaseReport("success_db", True, "All good")

    report = Report()
    report.databases = [success_db]
    notifier.report = report

    optimized_output = notifier.get_optimized_output()

    # Should be empty since no failures
    assert optimized_output == ""


def test_output_tail_truncation():
    """Test that output uses tail (last 10 lines) of logs."""
    notifier = TestNotifier()

    # Create output with many lines
    lines = [f"Line {i}" for i in range(20)]
    long_output = "\n".join(lines)

    failed_db = DatabaseReport("test_db", False, long_output)

    report = Report()
    report.databases = [failed_db]
    notifier.report = report

    optimized_output = notifier.get_optimized_output()

    # Should only contain last 10 lines
    assert "Line 10" in optimized_output
    assert "Line 19" in optimized_output
    assert "Line 0" not in optimized_output
    assert "Line 5" not in optimized_output


def test_failed_output_excludes_successful_databases():
    """Test that output only includes failed databases, not successful ones."""
    notifier = TestNotifier()

    # Mix of successful and failed databases
    success_db = DatabaseReport("success_db", True, "Success log content")
    failed_db = DatabaseReport("failed_db", False, "Error occurred")

    report = Report()
    report.databases = [success_db, failed_db]
    notifier.report = report

    optimized_output = notifier.get_optimized_output()

    # Output should only contain failed database output
    assert "Error occurred" in optimized_output
    assert "Success log content" not in optimized_output


def test_character_allocation_edge_case_zero_budget():
    """Test edge case where budget becomes zero or negative."""
    notifier = TestNotifier()
    notifier.max_output_chars = 10  # Very small budget

    # Create multiple databases with outputs that would exceed tiny budget
    db1 = DatabaseReport("database1", False, "Long error message")  # ~17 chars + prefix
    db2 = DatabaseReport("database2", False, "Another error")       # ~13 chars + prefix

    report = Report()
    report.databases = [db1, db2]
    notifier.report = report

    # Should not crash and should stay within budget
    optimized_output = notifier.get_optimized_output()
    assert len(optimized_output) <= 10


def test_platform_specific_character_limits():
    """Test that different notifier subclasses can have different character limits."""

    class SmallNotifier(TestNotifier):
        max_output_chars = 50

    class LargeNotifier(TestNotifier):
        max_output_chars = 200

    # Same test data for both
    long_output = "Error: " + "x" * 100
    failed_db = DatabaseReport("test_db", False, long_output)
    report = Report()
    report.databases = [failed_db]

    # Small notifier should truncate more aggressively
    small_notifier = SmallNotifier()
    small_notifier.report = report
    small_output = small_notifier.get_optimized_output()
    assert len(small_output) <= 50

    # Large notifier should preserve more content
    large_notifier = LargeNotifier()
    large_notifier.report = report
    large_output = large_notifier.get_optimized_output()
    assert len(large_output) <= 200
    assert len(large_output) > len(small_output)
