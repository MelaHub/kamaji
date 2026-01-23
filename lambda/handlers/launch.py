"""Handler for skill launch."""

import logging

from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_core.utils import is_request_type
from ask_sdk_model import Response

from .base import BaseHandler
import prompts

logger = logging.getLogger(__name__)


class LaunchRequestHandler(BaseHandler):
    """Handler for Skill Launch."""

    def can_handle(self, handler_input: HandlerInput) -> bool:
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        self.log_handler_entry(handler_input)

        speech = self.get_string(handler_input, prompts.LAUNCH_MESSAGE)
        return self.build_response(handler_input, speech, reprompt=speech)
