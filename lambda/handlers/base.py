"""Base handler class with common utilities."""

from abc import ABC
from typing import Any, Optional
import logging

from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response

logger = logging.getLogger(__name__)


class BaseHandler(AbstractRequestHandler, ABC):
    """
    Base class for all custom handlers providing common utilities.

    Provides:
    - Localization helpers
    - Attribute access helpers
    - Structured logging
    - Response building helpers
    """

    def get_string(self, handler_input: HandlerInput, key: str, **kwargs: Any) -> str:
        """
        Get a localized string with optional format parameters.

        Args:
            handler_input: Alexa handler input
            key: String key from prompts.py
            **kwargs: Format parameters for string interpolation

        Returns:
            Localized string, or key itself if not found
        """
        try:
            data = handler_input.attributes_manager.request_attributes.get("_", {})
            string = data.get(key, key)
            if kwargs:
                return string.format(**kwargs)
            return string
        except Exception as e:
            logger.error(f"Error getting localized string '{key}': {e}")
            return key

    def get_session_attr(
        self, handler_input: HandlerInput, key: str, default: Any = None
    ) -> Any:
        """Get a session attribute."""
        session_attr = handler_input.attributes_manager.session_attributes
        return session_attr.get(key, default)

    def set_session_attr(
        self, handler_input: HandlerInput, key: str, value: Any
    ) -> None:
        """Set a session attribute."""
        session_attr = handler_input.attributes_manager.session_attributes
        session_attr[key] = value

    def build_response(
        self,
        handler_input: HandlerInput,
        speech: str,
        reprompt: Optional[str] = None,
        end_session: bool = False
    ) -> Response:
        """
        Build a response with optional reprompt.

        Args:
            handler_input: Alexa handler input
            speech: Speech output text
            reprompt: Optional reprompt text (if provided, session stays open)
            end_session: Force end session even if reprompt provided

        Returns:
            Alexa Response object
        """
        builder = handler_input.response_builder.speak(speech)
        if reprompt and not end_session:
            builder.ask(reprompt)
        return builder.response

    def log_handler_entry(self, handler_input: HandlerInput) -> None:
        """Log handler entry with request details."""
        request = handler_input.request_envelope.request
        logger.info(
            f"Entering {self.__class__.__name__}",
            extra={
                'handler': self.__class__.__name__,
                'request_type': request.object_type,
                'locale': request.locale,
            }
        )
