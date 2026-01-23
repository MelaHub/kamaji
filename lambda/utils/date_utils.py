"""Date parsing utilities with proper error handling."""

from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DateParseError(Exception):
    """Raised when date parsing fails."""
    pass


def parse_date_slot(date_str: Optional[str]) -> datetime:
    """
    Parse an Alexa date slot value into a datetime object.

    Args:
        date_str: Date string in YYYY-MM-DD format from Alexa slot

    Returns:
        Parsed datetime object

    Raises:
        DateParseError: If date_str is None or invalid format
    """
    if date_str is None:
        logger.warning("Date slot value is None")
        raise DateParseError("Date value is missing")

    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError as e:
        logger.error(f"Failed to parse date '{date_str}': {e}")
        raise DateParseError(f"Invalid date format: {date_str}") from e


def format_event_day(dt: datetime) -> str:
    """
    Format datetime as month-day key for persistence.

    Args:
        dt: datetime object

    Returns:
        String in "M-D" format (e.g., "3-15" for March 15)
    """
    return f"{dt.month}-{dt.day}"


def format_event_year(dt: datetime) -> str:
    """
    Format datetime as year string for persistence.

    Args:
        dt: datetime object

    Returns:
        Year as string (e.g., "2024")
    """
    return str(dt.year)
