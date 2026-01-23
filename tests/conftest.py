"""Shared pytest fixtures for Alexa skill testing."""

import sys
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import MagicMock

import pytest

# Add lambda directory to path for imports
lambda_dir = Path(__file__).parent.parent / "lambda"
sys.path.insert(0, str(lambda_dir))


@pytest.fixture
def mock_handler_input():
    """Factory fixture to create mock HandlerInput objects."""

    def _create_handler_input(
        intent_name: Optional[str] = None,
        slots: Optional[Dict[str, str]] = None,
        session_attributes: Optional[Dict[str, Any]] = None,
        persistent_attributes: Optional[Dict[str, Any]] = None,
        locale: str = "it-IT",
        request_type: str = "IntentRequest"
    ) -> MagicMock:
        handler_input = MagicMock()

        # Mock request envelope
        request = MagicMock()
        request.object_type = request_type
        request.locale = locale
        request.request_id = "test-request-id"

        if intent_name:
            intent = MagicMock()
            intent.name = intent_name
            if slots:
                intent.slots = {
                    name: MagicMock(value=value)
                    for name, value in slots.items()
                }
            else:
                intent.slots = {}
            request.intent = intent

        handler_input.request_envelope = MagicMock()
        handler_input.request_envelope.request = request

        # Mock attributes manager
        attr_manager = MagicMock()
        attr_manager.session_attributes = session_attributes or {}
        attr_manager.persistent_attributes = persistent_attributes or {}
        attr_manager.request_attributes = {
            "_": {
                "SKILL_NAME": "Rigotti Home",
                "LAUNCH_MESSAGE": "Ciao! Come posso esserti utile?",
                "ADD_EVENT_PROMPT": "Cosa?",
                "EVENT_ADDED": "Fatto!",
                "ADD_ANOTHER_PROMPT": "Vuoi aggiungere un altro evento?",
                "NO_EVENTS_FOR_DATE": "Mi spiace, non ci sono stati eventi il {date}",
                "NO_EVENTS_FOUND": "Mi spiace. Non è successo niente il {date}",
                "EVENT_PROMPT": "Nel {year} {event}; cosa vuoi fare?",
                "NO_MORE_EVENTS": "Non ho trovato altri eventi!",
                "HELP_MESSAGE": "Puoi chiedermi di aggiungere, recuperare o modificare eventi.",
                "HELP_REPROMPT": "Come posso aiutarti?",
                "FALLBACK_MESSAGE": "Non posso aiutarti con questo.",
                "FALLBACK_REPROMPT": "Come posso aiutarti?",
                "ERROR_MESSAGE": "Spiacenti, si è verificato un errore.",
                "STOP_MESSAGE": "A presto!",
            }
        }
        handler_input.attributes_manager = attr_manager

        # Mock response builder
        response_builder = MagicMock()
        response_builder.speak.return_value = response_builder
        response_builder.ask.return_value = response_builder
        response_builder.set_card.return_value = response_builder
        response_builder.response = MagicMock()
        handler_input.response_builder = response_builder

        return handler_input

    return _create_handler_input


@pytest.fixture
def localization_data() -> Dict[str, str]:
    """Italian localization test data."""
    return {
        "SKILL_NAME": "Rigotti Home",
        "LAUNCH_MESSAGE": "Ciao! Come posso esserti utile?",
        "ADD_EVENT_PROMPT": "Cosa?",
        "EVENT_ADDED": "Fatto!",
        "ERROR_MESSAGE": "Spiacenti, si è verificato un errore.",
        "HELP_REPROMPT": "Come posso aiutarti?",
    }
