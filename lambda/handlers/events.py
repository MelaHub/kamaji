"""Handlers for event management (add, retrieve, modify, delete)."""

import logging
from typing import Dict, List, Optional, Tuple

from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_intent_name, get_slot_value
from ask_sdk_model import Response

from .base import BaseHandler
from constants import intents, slots, session_keys
from utils import (
    parse_date_slot,
    format_event_day,
    format_event_year,
    DateParseError,
    get_events_for_day,
    add_event_to_persistence,
    delete_event_from_persistence,
)
import prompts

logger = logging.getLogger(__name__)


class AddEventRequestHandler(BaseHandler):
    """Handler for initiating event addition flow."""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name(intents.ADD_EVENT_REQUEST)(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        self.log_handler_entry(handler_input)

        date_str = get_slot_value(handler_input=handler_input, slot_name=slots.DATE)

        if date_str is None:
            logger.warning("Date slot is missing in AddEventRequest")
            speech = self.get_string(handler_input, prompts.ERROR_MESSAGE)
            return self.build_response(handler_input, speech)

        self.set_session_attr(handler_input, session_keys.CURR_EVENT_DATE, date_str)

        speech = self.get_string(handler_input, prompts.ADD_EVENT_PROMPT)
        return self.build_response(handler_input, speech, reprompt=speech)


class AddEventTypeHandler(BaseHandler):
    """Handler for completing event addition with event description."""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name(intents.ADD_EVENT_TYPE)(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        self.log_handler_entry(handler_input)

        event = get_slot_value(handler_input=handler_input, slot_name=slots.EVENT)
        date_str = self.get_session_attr(handler_input, session_keys.CURR_EVENT_DATE)

        if date_str is None:
            logger.error("curr_event_date not found in session - flow broken")
            speech = self.get_string(handler_input, prompts.ERROR_MESSAGE)
            return self.build_response(handler_input, speech)

        try:
            event_date = parse_date_slot(date_str)
        except DateParseError as e:
            logger.error(f"Failed to parse stored date: {e}")
            speech = self.get_string(handler_input, prompts.ERROR_MESSAGE)
            return self.build_response(handler_input, speech)

        event_day = format_event_day(event_date)
        event_year = format_event_year(event_date)

        add_event_to_persistence(handler_input, event_day, event_year, event)

        speech = self.get_string(handler_input, prompts.EVENT_ADDED)
        reprompt = self.get_string(handler_input, prompts.ADD_ANOTHER_PROMPT)

        return self.build_response(handler_input, speech, reprompt=reprompt)


class RetrieveEventHandler(BaseHandler):
    """Handler for querying events by date."""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name(intents.RETRIEVE_EVENTS)(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        self.log_handler_entry(handler_input)

        date_str = get_slot_value(handler_input=handler_input, slot_name=slots.DATE)

        try:
            event_date = parse_date_slot(date_str)
        except DateParseError as e:
            logger.warning(f"Invalid date in RetrieveEvents: {e}")
            speech = self.get_string(handler_input, prompts.ERROR_MESSAGE)
            return self.build_response(handler_input, speech)

        event_day = format_event_day(event_date)
        events = get_events_for_day(handler_input, event_day)

        if not events:
            formatted_date = event_date.strftime('%d %B')
            speech = self.get_string(
                handler_input, prompts.NO_EVENTS_FOUND, date=formatted_date
            )
            return self.build_response(handler_input, speech)

        # Build speech listing all events by year
        parts = []
        for year in sorted(events.keys()):
            year_events = "; ".join(events[year])
            parts.append(f"Nel {year} {year_events}.")
        speech = " ".join(parts)

        return self.build_response(handler_input, speech)


class ModifyEventsRequestHandler(BaseHandler):
    """Handler for initiating event modification flow."""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name(intents.MODIFY_EVENTS_REQUEST)(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        self.log_handler_entry(handler_input)

        date_str = get_slot_value(handler_input=handler_input, slot_name=slots.DATE)

        try:
            event_date = parse_date_slot(date_str)
        except DateParseError as e:
            logger.warning(f"Invalid date in ModifyEventsRequest: {e}")
            speech = self.get_string(handler_input, prompts.ERROR_MESSAGE)
            return self.build_response(handler_input, speech)

        event_day = format_event_day(event_date)
        events = get_events_for_day(handler_input, event_day)

        if not events:
            speech = self.get_string(
                handler_input, prompts.NO_EVENTS_FOR_DATE, date=event_day
            )
            return self.build_response(handler_input, speech)

        # Initialize navigation state
        self.set_session_attr(handler_input, session_keys.EVENT_DAY, event_day)
        self.set_session_attr(handler_input, session_keys.CURR_YEAR_IDX, 0)
        self.set_session_attr(handler_input, session_keys.CURR_EVENT_IDX, 0)

        years = sorted(events.keys())
        curr_year = years[0]
        curr_events = events[curr_year]

        if not curr_events:
            speech = self.get_string(handler_input, prompts.NO_MORE_EVENTS)
            return self.build_response(handler_input, speech)

        speech = self.get_string(
            handler_input, prompts.EVENT_PROMPT,
            year=curr_year, event=curr_events[0]
        )
        return self.build_response(handler_input, speech, reprompt=speech)


def _get_event_navigation_context(
    handler_input: HandlerInput
) -> Optional[Tuple[str, Dict[str, List[str]], List[str], int, int]]:
    """
    Get the current event navigation context from session.

    Returns:
        Tuple of (event_day, events_dict, years_list, year_idx, event_idx)
        or None if not in navigation context.
    """
    session_attr = handler_input.attributes_manager.session_attributes
    event_day = session_attr.get(session_keys.EVENT_DAY)

    if event_day is None:
        return None

    persistence_attr = handler_input.attributes_manager.persistent_attributes
    events = persistence_attr.get(event_day, {})

    if not events:
        return None

    years = sorted(events.keys())
    year_idx = session_attr.get(session_keys.CURR_YEAR_IDX, 0)
    event_idx = session_attr.get(session_keys.CURR_EVENT_IDX, 0)

    return event_day, events, years, year_idx, event_idx


class NextEventHandler(BaseHandler):
    """Handler for navigating to next event."""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name(intents.NEXT_EVENT)(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        self.log_handler_entry(handler_input)

        context = _get_event_navigation_context(handler_input)
        if context is None:
            speech = self.get_string(handler_input, prompts.ERROR_MESSAGE)
            return self.build_response(handler_input, speech)

        event_day, events, years, year_idx, event_idx = context
        curr_year = years[year_idx]
        curr_events = events[curr_year]

        # Try to move to next event in current year
        if len(curr_events) > event_idx + 1:
            new_event_idx = event_idx + 1
            self.set_session_attr(
                handler_input, session_keys.CURR_EVENT_IDX, new_event_idx
            )
            speech = self.get_string(
                handler_input, prompts.EVENT_PROMPT,
                year=curr_year, event=curr_events[new_event_idx]
            )
            return self.build_response(handler_input, speech, reprompt=speech)

        # Try to move to next year
        if len(years) > year_idx + 1:
            new_year_idx = year_idx + 1
            new_year = years[new_year_idx]
            new_events = events[new_year]

            self.set_session_attr(
                handler_input, session_keys.CURR_YEAR_IDX, new_year_idx
            )
            self.set_session_attr(handler_input, session_keys.CURR_EVENT_IDX, 0)

            speech = self.get_string(
                handler_input, prompts.EVENT_PROMPT,
                year=new_year, event=new_events[0]
            )
            return self.build_response(handler_input, speech, reprompt=speech)

        # No more events
        speech = self.get_string(handler_input, prompts.NO_MORE_EVENTS)
        return self.build_response(handler_input, speech)


class PreviousEventHandler(BaseHandler):
    """Handler for navigating to previous event."""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name(intents.PREVIOUS_EVENT)(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        self.log_handler_entry(handler_input)

        context = _get_event_navigation_context(handler_input)
        if context is None:
            speech = self.get_string(handler_input, prompts.ERROR_MESSAGE)
            return self.build_response(handler_input, speech)

        event_day, events, years, year_idx, event_idx = context
        curr_year = years[year_idx]

        # Try to move to previous event in current year
        if event_idx > 0:
            new_event_idx = event_idx - 1
            self.set_session_attr(
                handler_input, session_keys.CURR_EVENT_IDX, new_event_idx
            )
            speech = self.get_string(
                handler_input, prompts.EVENT_PROMPT,
                year=curr_year, event=events[curr_year][new_event_idx]
            )
            return self.build_response(handler_input, speech, reprompt=speech)

        # Try to move to previous year
        if year_idx > 0:
            new_year_idx = year_idx - 1
            new_year = years[new_year_idx]
            new_events = events[new_year]
            new_event_idx = len(new_events) - 1  # Last event of previous year

            self.set_session_attr(
                handler_input, session_keys.CURR_YEAR_IDX, new_year_idx
            )
            self.set_session_attr(
                handler_input, session_keys.CURR_EVENT_IDX, new_event_idx
            )

            speech = self.get_string(
                handler_input, prompts.EVENT_PROMPT,
                year=new_year, event=new_events[new_event_idx]
            )
            return self.build_response(handler_input, speech, reprompt=speech)

        # No previous events
        speech = self.get_string(handler_input, prompts.NO_PREVIOUS_EVENTS)
        return self.build_response(handler_input, speech)


class DeleteEventHandler(BaseHandler):
    """Handler for initiating delete with confirmation."""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name(intents.DELETE_EVENT)(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        self.log_handler_entry(handler_input)

        context = _get_event_navigation_context(handler_input)
        if context is None:
            speech = self.get_string(handler_input, prompts.ERROR_MESSAGE)
            return self.build_response(handler_input, speech)

        event_day, events, years, year_idx, event_idx = context
        curr_year = years[year_idx]
        curr_event = events[curr_year][event_idx]

        # Set pending delete flag and ask for confirmation
        self.set_session_attr(handler_input, session_keys.PENDING_DELETE, True)

        speech = self.get_string(
            handler_input, prompts.DELETE_CONFIRM_PROMPT, event=curr_event
        )
        return self.build_response(handler_input, speech, reprompt=speech)


class ConfirmDeleteHandler(BaseHandler):
    """Handler for confirming delete (AMAZON.YesIntent)."""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        pending = self.get_session_attr(handler_input, session_keys.PENDING_DELETE)
        return is_intent_name(intents.AMAZON_YES)(handler_input) and pending

    def handle(self, handler_input: HandlerInput) -> Response:
        self.log_handler_entry(handler_input)

        # Clear pending delete flag
        self.set_session_attr(handler_input, session_keys.PENDING_DELETE, False)

        context = _get_event_navigation_context(handler_input)
        if context is None:
            speech = self.get_string(handler_input, prompts.ERROR_MESSAGE)
            return self.build_response(handler_input, speech)

        event_day, events, years, year_idx, event_idx = context
        curr_year = years[year_idx]

        # Delete the event
        remaining_events = delete_event_from_persistence(
            handler_input, event_day, curr_year, event_idx
        )

        deleted_speech = self.get_string(handler_input, prompts.EVENT_DELETED)

        # Try to show next event in same year
        if remaining_events and len(remaining_events) > event_idx:
            next_event_speech = self.get_string(
                handler_input, prompts.EVENT_PROMPT,
                year=curr_year, event=remaining_events[event_idx]
            )
            speech = f"{deleted_speech} {next_event_speech}"
            return self.build_response(handler_input, speech, reprompt=next_event_speech)

        # Try to show first event in same year (if we deleted the last one)
        if remaining_events:
            self.set_session_attr(handler_input, session_keys.CURR_EVENT_IDX, 0)
            next_event_speech = self.get_string(
                handler_input, prompts.EVENT_PROMPT,
                year=curr_year, event=remaining_events[0]
            )
            speech = f"{deleted_speech} {next_event_speech}"
            return self.build_response(handler_input, speech, reprompt=next_event_speech)

        # Try to move to next year
        if len(years) > year_idx + 1:
            new_year_idx = year_idx + 1
            new_year = years[new_year_idx]

            # Re-fetch events after deletion
            persistence_attr = handler_input.attributes_manager.persistent_attributes
            updated_events = persistence_attr.get(event_day, {})
            new_events = updated_events.get(new_year, [])

            if new_events:
                self.set_session_attr(
                    handler_input, session_keys.CURR_YEAR_IDX, new_year_idx
                )
                self.set_session_attr(handler_input, session_keys.CURR_EVENT_IDX, 0)

                next_event_speech = self.get_string(
                    handler_input, prompts.EVENT_PROMPT,
                    year=new_year, event=new_events[0]
                )
                speech = f"{deleted_speech} {next_event_speech}"
                return self.build_response(handler_input, speech, reprompt=next_event_speech)

        # No more events
        no_more_speech = self.get_string(handler_input, prompts.NO_MORE_EVENTS)
        speech = f"{deleted_speech} {no_more_speech}"
        return self.build_response(handler_input, speech)


class CancelDeleteHandler(BaseHandler):
    """Handler for cancelling delete (AMAZON.NoIntent)."""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        pending = self.get_session_attr(handler_input, session_keys.PENDING_DELETE)
        return is_intent_name(intents.AMAZON_NO)(handler_input) and pending

    def handle(self, handler_input: HandlerInput) -> Response:
        self.log_handler_entry(handler_input)

        # Clear pending delete flag
        self.set_session_attr(handler_input, session_keys.PENDING_DELETE, False)

        speech = self.get_string(handler_input, prompts.DELETE_CANCELLED)
        return self.build_response(handler_input, speech, reprompt=speech)
