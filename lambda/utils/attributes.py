"""Helper functions for session and persistence attribute management."""

from typing import Any, Dict, List, Optional, TypeVar
import logging

from ask_sdk_core.handler_input import HandlerInput

logger = logging.getLogger(__name__)

T = TypeVar('T')


def get_session_attr(handler_input: HandlerInput, key: str, default: T = None) -> T:
    """
    Safely get a session attribute.

    Args:
        handler_input: Alexa handler input
        key: Session attribute key
        default: Default value if key not found

    Returns:
        The attribute value or default
    """
    session_attr = handler_input.attributes_manager.session_attributes
    return session_attr.get(key, default)


def set_session_attr(handler_input: HandlerInput, key: str, value: Any) -> None:
    """
    Set a session attribute.

    Args:
        handler_input: Alexa handler input
        key: Session attribute key
        value: Value to set
    """
    session_attr = handler_input.attributes_manager.session_attributes
    session_attr[key] = value


def get_persistent_attr(handler_input: HandlerInput) -> Dict[str, Any]:
    """
    Get all persistent attributes.

    Args:
        handler_input: Alexa handler input

    Returns:
        Dictionary of persistent attributes
    """
    return handler_input.attributes_manager.persistent_attributes


def get_events_for_day(handler_input: HandlerInput, event_day: str) -> Dict[str, List[str]]:
    """
    Get all events for a specific day from persistence.

    Args:
        handler_input: Alexa handler input
        event_day: Day key in "M-D" format

    Returns:
        Dict mapping year -> list of events, empty dict if none found
    """
    persistence_attr = handler_input.attributes_manager.persistent_attributes
    return persistence_attr.get(event_day, {})


def add_event_to_persistence(
    handler_input: HandlerInput,
    event_day: str,
    event_year: str,
    event: str
) -> None:
    """
    Add an event to persistent storage.

    Args:
        handler_input: Alexa handler input
        event_day: Day key in "M-D" format
        event_year: Year as string
        event: Event description
    """
    persistence_attr = handler_input.attributes_manager.persistent_attributes
    persistence_attr.setdefault(event_day, {}).setdefault(event_year, []).append(event)
    handler_input.attributes_manager.save_persistent_attributes()
    logger.info(f"Added event to {event_day}/{event_year}: {event}")


def delete_event_from_persistence(
    handler_input: HandlerInput,
    event_day: str,
    event_year: str,
    event_idx: int
) -> List[str]:
    """
    Delete an event from persistent storage.

    Args:
        handler_input: Alexa handler input
        event_day: Day key in "M-D" format
        event_year: Year as string
        event_idx: Index of event to delete

    Returns:
        Remaining events for that year after deletion
    """
    persistence_attr = handler_input.attributes_manager.persistent_attributes
    events = persistence_attr.get(event_day, {})

    if event_year not in events:
        logger.warning(f"Year {event_year} not found for day {event_day}")
        return []

    year_events = events[event_year]
    remaining_events = [e for i, e in enumerate(year_events) if i != event_idx]

    if remaining_events:
        persistence_attr[event_day][event_year] = remaining_events
    else:
        # Remove the year if no events left
        persistence_attr[event_day].pop(event_year, None)
        # Remove the day if no years left
        if not persistence_attr[event_day]:
            persistence_attr.pop(event_day, None)

    handler_input.attributes_manager.save_persistent_attributes()
    logger.info(f"Deleted event at index {event_idx} from {event_day}/{event_year}")

    return remaining_events


def update_event_in_persistence(
    handler_input: HandlerInput,
    event_day: str,
    event_year: str,
    event_idx: int,
    new_event: str
) -> bool:
    """
    Update an event in persistent storage.

    Args:
        handler_input: Alexa handler input
        event_day: Day key in "M-D" format
        event_year: Year as string
        event_idx: Index of event to update
        new_event: New event description

    Returns:
        True if updated successfully, False otherwise
    """
    persistence_attr = handler_input.attributes_manager.persistent_attributes
    events = persistence_attr.get(event_day, {})

    if event_year not in events:
        logger.warning(f"Year {event_year} not found for day {event_day}")
        return False

    year_events = events[event_year]
    if event_idx >= len(year_events):
        logger.warning(f"Event index {event_idx} out of range for {event_day}/{event_year}")
        return False

    persistence_attr[event_day][event_year][event_idx] = new_event
    handler_input.attributes_manager.save_persistent_attributes()
    logger.info(f"Updated event at index {event_idx} in {event_day}/{event_year}: {new_event}")

    return True
