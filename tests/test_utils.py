"""Tests for utility functions."""

import pytest
from datetime import datetime

from utils.date_utils import (
    parse_date_slot,
    format_event_day,
    format_event_year,
    DateParseError,
)


class TestParseDateSlot:
    """Tests for parse_date_slot function."""

    def test_parses_valid_date(self):
        """Should parse valid YYYY-MM-DD format."""
        result = parse_date_slot("2024-03-15")
        assert result == datetime(2024, 3, 15)

    def test_parses_single_digit_month_day(self):
        """Should parse dates with single digit month and day."""
        result = parse_date_slot("2024-01-05")
        assert result == datetime(2024, 1, 5)

    def test_raises_on_none(self):
        """Should raise DateParseError when input is None."""
        with pytest.raises(DateParseError, match="Date value is missing"):
            parse_date_slot(None)

    def test_raises_on_invalid_format(self):
        """Should raise DateParseError on invalid format."""
        with pytest.raises(DateParseError, match="Invalid date format"):
            parse_date_slot("15/03/2024")

    def test_raises_on_invalid_date(self):
        """Should raise DateParseError on impossible date."""
        with pytest.raises(DateParseError):
            parse_date_slot("2024-02-30")

    def test_raises_on_empty_string(self):
        """Should raise DateParseError on empty string."""
        with pytest.raises(DateParseError):
            parse_date_slot("")


class TestFormatEventDay:
    """Tests for format_event_day function."""

    def test_formats_correctly(self):
        """Should format as month-day."""
        dt = datetime(2024, 3, 15)
        assert format_event_day(dt) == "3-15"

    def test_single_digit_month_day(self):
        """Should not zero-pad single digits."""
        dt = datetime(2024, 1, 5)
        assert format_event_day(dt) == "1-5"

    def test_december_date(self):
        """Should handle December dates."""
        dt = datetime(2024, 12, 31)
        assert format_event_day(dt) == "12-31"


class TestFormatEventYear:
    """Tests for format_event_year function."""

    def test_formats_correctly(self):
        """Should format as year string."""
        dt = datetime(2024, 3, 15)
        assert format_event_year(dt) == "2024"

    def test_different_years(self):
        """Should work for different years."""
        assert format_event_year(datetime(2020, 1, 1)) == "2020"
        assert format_event_year(datetime(2030, 12, 31)) == "2030"
