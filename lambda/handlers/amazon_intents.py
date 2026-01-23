"""Handlers for Amazon built-in intents."""

import logging

from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_intent_name, is_request_type
from ask_sdk_model import Response
from ask_sdk_model.ui import SimpleCard

from .base import BaseHandler
from constants import intents
import prompts

logger = logging.getLogger(__name__)


class HelpIntentHandler(BaseHandler):
    """Handler for Help Intent."""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name(intents.AMAZON_HELP)(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        self.log_handler_entry(handler_input)

        speech = self.get_string(handler_input, prompts.HELP_MESSAGE)
        reprompt = self.get_string(handler_input, prompts.HELP_REPROMPT)
        skill_name = self.get_string(handler_input, prompts.SKILL_NAME)

        return (
            handler_input.response_builder
            .speak(speech)
            .ask(reprompt)
            .set_card(SimpleCard(skill_name, speech))
            .response
        )


class CancelOrStopIntentHandler(BaseHandler):
    """Single handler for Cancel and Stop Intent."""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return (
            is_intent_name(intents.AMAZON_CANCEL)(handler_input) or
            is_intent_name(intents.AMAZON_STOP)(handler_input)
        )

    def handle(self, handler_input: HandlerInput) -> Response:
        self.log_handler_entry(handler_input)

        speech = self.get_string(handler_input, prompts.STOP_MESSAGE)
        return self.build_response(handler_input, speech, end_session=True)


class FallbackIntentHandler(BaseHandler):
    """Handler for Fallback Intent."""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_intent_name(intents.AMAZON_FALLBACK)(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        self.log_handler_entry(handler_input)

        speech = self.get_string(handler_input, prompts.FALLBACK_MESSAGE)
        reprompt = self.get_string(handler_input, prompts.FALLBACK_REPROMPT)

        return self.build_response(handler_input, speech, reprompt=reprompt)


class SessionEndedRequestHandler(BaseHandler):
    """Handler for Session End."""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        self.log_handler_entry(handler_input)

        reason = handler_input.request_envelope.request.reason
        logger.info(f"Session ended reason: {reason}")

        return handler_input.response_builder.response
