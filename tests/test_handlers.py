"""Tests for request handlers."""

import pytest
from unittest.mock import patch, MagicMock

from handlers.base import BaseHandler
from handlers.launch import LaunchRequestHandler
from handlers.events import AddEventRequestHandler, AddEventTypeHandler
from handlers.amazon_intents import HelpIntentHandler, CancelOrStopIntentHandler
from exceptions.handlers import CatchAllExceptionHandler
from constants import session_keys
import prompts


class TestBaseHandler:
    """Tests for BaseHandler utility methods."""

    def test_get_string_returns_localized_string(self, mock_handler_input):
        """Should return localized string from request attributes."""
        handler_input = mock_handler_input()

        class TestHandler(BaseHandler):
            def can_handle(self, h): return True
            def handle(self, h): pass

        handler = TestHandler()
        result = handler.get_string(handler_input, prompts.LAUNCH_MESSAGE)
        assert result == "Ciao! Come posso esserti utile?"

    def test_get_string_with_format_params(self, mock_handler_input):
        """Should format string with provided parameters."""
        handler_input = mock_handler_input()

        class TestHandler(BaseHandler):
            def can_handle(self, h): return True
            def handle(self, h): pass

        handler = TestHandler()
        result = handler.get_string(
            handler_input, prompts.EVENT_PROMPT,
            year="2024", event="compleanno"
        )
        assert "2024" in result
        assert "compleanno" in result

    def test_get_string_returns_key_on_missing(self, mock_handler_input):
        """Should return key itself if not found in localization."""
        handler_input = mock_handler_input()
        handler_input.attributes_manager.request_attributes["_"] = {}

        class TestHandler(BaseHandler):
            def can_handle(self, h): return True
            def handle(self, h): pass

        handler = TestHandler()
        result = handler.get_string(handler_input, "NONEXISTENT_KEY")
        assert result == "NONEXISTENT_KEY"

    def test_get_session_attr(self, mock_handler_input):
        """Should get session attribute."""
        handler_input = mock_handler_input(
            session_attributes={"test_key": "test_value"}
        )

        class TestHandler(BaseHandler):
            def can_handle(self, h): return True
            def handle(self, h): pass

        handler = TestHandler()
        result = handler.get_session_attr(handler_input, "test_key")
        assert result == "test_value"

    def test_get_session_attr_default(self, mock_handler_input):
        """Should return default if key not found."""
        handler_input = mock_handler_input()

        class TestHandler(BaseHandler):
            def can_handle(self, h): return True
            def handle(self, h): pass

        handler = TestHandler()
        result = handler.get_session_attr(handler_input, "missing", "default")
        assert result == "default"

    def test_set_session_attr(self, mock_handler_input):
        """Should set session attribute."""
        handler_input = mock_handler_input()

        class TestHandler(BaseHandler):
            def can_handle(self, h): return True
            def handle(self, h): pass

        handler = TestHandler()
        handler.set_session_attr(handler_input, "new_key", "new_value")
        assert handler_input.attributes_manager.session_attributes["new_key"] == "new_value"


class TestLaunchRequestHandler:
    """Tests for LaunchRequestHandler."""

    def test_handle_returns_greeting(self, mock_handler_input):
        """Handler should return greeting message."""
        handler_input = mock_handler_input(request_type="LaunchRequest")
        handler = LaunchRequestHandler()

        handler.handle(handler_input)

        handler_input.response_builder.speak.assert_called_once()
        call_args = handler_input.response_builder.speak.call_args[0][0]
        assert "Ciao" in call_args


class TestAddEventRequestHandler:
    """Tests for AddEventRequestHandler."""

    def test_stores_date_in_session(self, mock_handler_input):
        """Handler should store date slot in session attributes."""
        handler_input = mock_handler_input(
            intent_name="AddEventRequest",
            slots={"date": "2024-03-15"}
        )
        handler = AddEventRequestHandler()

        with patch(
            'handlers.events.get_slot_value',
            return_value="2024-03-15"
        ):
            handler.handle(handler_input)

        assert handler_input.attributes_manager.session_attributes[
            session_keys.CURR_EVENT_DATE
        ] == "2024-03-15"

    def test_handles_missing_date(self, mock_handler_input):
        """Handler should return error when date slot is missing."""
        handler_input = mock_handler_input(intent_name="AddEventRequest")
        handler = AddEventRequestHandler()

        with patch('handlers.events.get_slot_value', return_value=None):
            handler.handle(handler_input)

        handler_input.response_builder.speak.assert_called_once()


class TestAddEventTypeHandler:
    """Tests for AddEventTypeHandler."""

    def test_saves_event_to_persistence(self, mock_handler_input):
        """Handler should save event to persistent attributes."""
        handler_input = mock_handler_input(
            intent_name="AddEventType",
            slots={"event": "compleanno di Mario"},
            session_attributes={session_keys.CURR_EVENT_DATE: "2024-03-15"}
        )
        handler = AddEventTypeHandler()

        with patch(
            'handlers.events.get_slot_value',
            return_value="compleanno di Mario"
        ):
            handler.handle(handler_input)

        handler_input.attributes_manager.save_persistent_attributes.assert_called_once()

    def test_handles_missing_session_date(self, mock_handler_input):
        """Handler should error gracefully when session date is missing."""
        handler_input = mock_handler_input(
            intent_name="AddEventType",
            slots={"event": "test event"},
            session_attributes={}
        )
        handler = AddEventTypeHandler()

        with patch('handlers.events.get_slot_value', return_value="test"):
            handler.handle(handler_input)

        # Should return error response
        handler_input.response_builder.speak.assert_called_once()


class TestCatchAllExceptionHandler:
    """Tests for CatchAllExceptionHandler."""

    def test_can_handle_any_exception(self, mock_handler_input):
        """Handler should handle any exception."""
        handler_input = mock_handler_input()
        handler = CatchAllExceptionHandler()

        assert handler.can_handle(handler_input, ValueError("test"))
        assert handler.can_handle(handler_input, RuntimeError("test"))
        assert handler.can_handle(handler_input, Exception("test"))

    def test_returns_error_message(self, mock_handler_input):
        """Handler should return localized error message."""
        handler_input = mock_handler_input()
        handler = CatchAllExceptionHandler()

        handler.handle(handler_input, Exception("test error"))

        handler_input.response_builder.speak.assert_called_once()
        call_args = handler_input.response_builder.speak.call_args[0][0]
        assert "errore" in call_args.lower()

    def test_fallback_when_localization_missing(self, mock_handler_input):
        """Handler should use fallback when localization fails."""
        handler_input = mock_handler_input()
        handler_input.attributes_manager.request_attributes = {}
        handler = CatchAllExceptionHandler()

        handler.handle(handler_input, Exception("test"))

        handler_input.response_builder.speak.assert_called_once()
