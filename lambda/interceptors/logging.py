"""Request and response logging interceptors."""

import logging

from ask_sdk_core.dispatch_components import (
    AbstractRequestInterceptor,
    AbstractResponseInterceptor,
)
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response

logger = logging.getLogger(__name__)


class RequestLogger(AbstractRequestInterceptor):
    """Log incoming Alexa requests."""

    def process(self, handler_input: HandlerInput) -> None:
        logger.debug(f"Alexa Request: {handler_input.request_envelope.request}")


class ResponseLogger(AbstractResponseInterceptor):
    """Log outgoing Alexa responses."""

    def process(self, handler_input: HandlerInput, response: Response) -> None:
        logger.debug(f"Alexa Response: {response}")
