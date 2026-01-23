"""Exception handlers for the skill."""

import logging

from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response

import prompts

logger = logging.getLogger(__name__)

# Fallback messages in case localization fails
FALLBACK_ERROR_MESSAGE = "Mi dispiace, si è verificato un errore."
FALLBACK_HELP_REPROMPT = "Come posso aiutarti?"


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """
    Catch-all exception handler.

    Logs the exception and returns a user-friendly error message.
    """

    def can_handle(self, handler_input: HandlerInput, exception: Exception) -> bool:
        return True

    def handle(self, handler_input: HandlerInput, exception: Exception) -> Response:
        logger.error(
            f"Exception in handler: {exception}",
            exc_info=True,
            extra={
                'exception_type': type(exception).__name__,
                'request_id': handler_input.request_envelope.request.request_id,
            }
        )

        # Safely get localization data with fallback
        try:
            data = handler_input.attributes_manager.request_attributes.get("_", {})
            error_message = data.get(prompts.ERROR_MESSAGE, FALLBACK_ERROR_MESSAGE)
            help_reprompt = data.get(prompts.HELP_REPROMPT, FALLBACK_HELP_REPROMPT)
        except Exception:
            # Ultimate fallback if localization fails
            error_message = FALLBACK_ERROR_MESSAGE
            help_reprompt = FALLBACK_HELP_REPROMPT

        return (
            handler_input.response_builder
            .speak(error_message)
            .ask(help_reprompt)
            .response
        )
