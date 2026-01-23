"""Intent name constants matching interaction model."""

from typing import Final

# Custom intents
ADD_EVENT_REQUEST: Final[str] = "AddEventRequest"
ADD_EVENT_TYPE: Final[str] = "AddEventType"
RETRIEVE_EVENTS: Final[str] = "RetrieveEvents"
MODIFY_EVENTS_REQUEST: Final[str] = "ModifyEventsRequest"
NEXT_EVENT: Final[str] = "NextEvent"
DELETE_EVENT: Final[str] = "DeleteEvent"

# Amazon built-in intents
AMAZON_HELP: Final[str] = "AMAZON.HelpIntent"
AMAZON_CANCEL: Final[str] = "AMAZON.CancelIntent"
AMAZON_STOP: Final[str] = "AMAZON.StopIntent"
AMAZON_FALLBACK: Final[str] = "AMAZON.FallbackIntent"
