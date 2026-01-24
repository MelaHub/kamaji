"""Session attribute key constants to eliminate magic strings."""

from typing import Final

# Event flow session keys
CURR_EVENT_DATE: Final[str] = "curr_event_date"
EVENT_DAY: Final[str] = "event_day"
CURR_YEAR_IDX: Final[str] = "curr_year_idx"
CURR_EVENT_IDX: Final[str] = "curr_event_idx"

# Delete confirmation
PENDING_DELETE: Final[str] = "pending_delete"
