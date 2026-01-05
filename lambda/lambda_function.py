# -*- coding: utf-8 -*-

from datetime import date, datetime, timedelta
import logging
import json
import prompts
import os
import boto3

from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_dynamodb.adapter import DynamoDbAdapter

import ask_sdk_core.utils as ask_utils
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import (
    AbstractRequestHandler, AbstractExceptionHandler,
    AbstractRequestInterceptor, AbstractResponseInterceptor)
from ask_sdk_core.utils import is_request_type, is_intent_name, get_slot_value
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model.ui import SimpleCard
from ask_sdk_model import Response

sb = SkillBuilder()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ddb_region = os.environ.get('DYNAMODB_PERSISTENCE_REGION', 'eu-west')
ddb_table_name = os.environ.get('DYNAMODB_PERSISTENCE_TABLE_NAME', '96f3bf44-3a7b-448a-ab9b-96085cfa0ca6')

ddb_resource = boto3.resource('dynamodb', region_name=ddb_region)
dynamodb_adapter = DynamoDbAdapter(table_name=ddb_table_name, create_table=False, dynamodb_resource=ddb_resource)

class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        speak_output = "Ciao! Come posso esserti utile?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class GetTimeToHomeHandler(AbstractRequestHandler):
    """Handler for Skill GetTimeToHome, that tells how much time is left before the house is ready."""
    
    base_date = date(2022, 7, 31)
    worst_case_date = base_date + timedelta(days=120)

    def can_handle(self, handler_input):
        return is_intent_name("GetTimeToHome")(handler_input)

    def handle(self, handler_input):        
        t = date.today()

        speech = f"Mancano ancora {(self.base_date - t).days} giorni alla data prevista di consegna. Se proprio siete sfigati, {(self.worst_case_date - t).days}"

        handler_input.response_builder.speak(speech)
        
        return handler_input.response_builder.response


class AddEventRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch and AddEventRequest Intent."""

    def can_handle(self, handler_input):
        return is_intent_name("AddEventRequest")(handler_input)

    def handle(self, handler_input):
        date = get_slot_value(
            handler_input=handler_input, slot_name="date")
        
        session_attr = handler_input.attributes_manager.session_attributes
        session_attr["curr_event_date"] = date
        
        speak_output = "Cosa?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class AddEventTypeHandler(AbstractRequestHandler):
    """Handler for Skill Launch and AddEventType Intent."""
    
    def can_handle(self, handler_input):
        return is_intent_name("AddEventType")(handler_input)

    def handle(self, handler_input):
        event = get_slot_value(
            handler_input=handler_input, slot_name="event")
        
        curr_event_date_str = handler_input.attributes_manager.session_attributes.get("curr_event_date")

        curr_event_date = datetime.strptime(curr_event_date_str, "%Y-%m-%d")

        event_year = f"{curr_event_date.year}"
        event_day = f"{curr_event_date.month}-{curr_event_date.day}"

        persistence_attributes = handler_input.attributes_manager.persistent_attributes
        persistence_attributes.setdefault(event_day, {}).setdefault(event_year, []).append(event)

        handler_input.attributes_manager.save_persistent_attributes()
        
        return (
            handler_input.response_builder
                .speak("Fatto!")
                .ask("Vuoi aggiungere un altro evento?") 
                .response
        )

class ModifyEventsRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch and ModifyEventsRequest Intent."""

    def can_handle(self, handler_input):
        return is_intent_name("ModifyEventsRequest")(handler_input)

    def handle(self, handler_input):

        event_date_str = get_slot_value(handler_input=handler_input, slot_name="date")

        event_date = datetime.strptime(event_date_str, "%Y-%m-%d")
        event_day = f"{event_date.month}-{event_date.day}"

        persistence_attributes = handler_input.attributes_manager.persistent_attributes

        events = persistence_attributes.get(event_day, {})

        if not events:
            return (
                handler_input.response_builder
                    .speak(f"Mi spiace, non ci sono stati eventi il {event_day}")
                    .response
            )

        session_attr = handler_input.attributes_manager.session_attributes
        session_attr["event_day"] = event_day
        
        year_index = 0
        event_index = 0
        session_attr["curr_year_idx"] = year_index
        session_attr["curr_event_idx"] = event_index

        curr_year = list(sorted(events.keys()))[year_index]
        curr_events = events[curr_year]
        # TODO: here I'm giving for granted that I have at least 1 event

        speak_output = f"Nel {curr_year} {curr_events[event_index]}; cosa vuoi fare?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class NextEventHandler(AbstractRequestHandler):
    """Handler for Skill Launch and NextEvent Intent."""
    
    def can_handle(self, handler_input):
        return is_intent_name("NextEvent")(handler_input)

    def handle(self, handler_input):
        session_attr = handler_input.attributes_manager.session_attributes
        event_day = session_attr.get("event_day")
        curr_year_idx = session_attr.get("curr_year_idx")
        curr_event_idx = session_attr.get("curr_event_idx")

        persistence_attributes = handler_input.attributes_manager.persistent_attributes
        events = persistence_attributes[event_day]

        years = list(sorted(events.keys()))

        curr_year = years[curr_year_idx]
        curr_events = events[curr_year]

        if len(curr_events) > curr_event_idx + 1:
            # There's an event
            session_attr["curr_event_idx"] = curr_event_idx + 1
            speak_output = f"Nel {curr_year} {curr_events[curr_event_idx + 1]}; cosa vuoi fare?"
        else:
            # Let's find another year
            if len(years) > curr_year_idx + 1:
                curr_year = years[curr_year_idx + 1]
                curr_events = events[curr_year]
                session_attr["curr_year_idx"] = curr_year_idx + 1
                session_attr["curr_event_idx"] = 0
                speak_output = f"Nel {curr_year} {curr_events[0]}; cosa vuoi fare?"
            else:
                return (
                    handler_input.response_builder
                        .speak("Non ho trovato altri eventi!")
                        .response
                )
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output) 
                .response
        )


class DeleteEventHandler(AbstractRequestHandler):
    """Handler for Skill Launch and DeleteEvent Intent."""
    
    def can_handle(self, handler_input):
        return is_intent_name("DeleteEvent")(handler_input)

    def handle(self, handler_input):
        session_attr = handler_input.attributes_manager.session_attributes
        event_day = session_attr.get("event_day")
        curr_year_idx = session_attr.get("curr_year_idx")
        curr_event_idx = session_attr.get("curr_event_idx")

        persistence_attributes = handler_input.attributes_manager.persistent_attributes
        events = persistence_attributes[event_day]

        years = list(sorted(events.keys()))

        curr_year = years[curr_year_idx]
        curr_events = [event for (i, event) in enumerate(events[curr_year]) if i != curr_event_idx]
        
        if curr_events:
            persistence_attributes.setdefault(event_day, {})[curr_year] = curr_events
        else:
            persistence_attributes[event_day].pop(curr_year)

        handler_input.attributes_manager.save_persistent_attributes()

        if len(curr_events) > curr_event_idx:
            # There's an event next
            speak_output = f"Nel {curr_year} {curr_events[curr_event_idx]}; cosa vuoi fare?"
        else:
            # Let's find another year
            if len(years) > curr_year_idx + 1:
                curr_year = years[curr_year_idx + 1]
                if curr_year in persistence_attributes[event_day]:
                    session_attr["curr_year_idx"] = curr_year_idx + 1
                curr_events = events[curr_year]                
                session_attr["curr_event_idx"] = 0
                speak_output = f"Nel {curr_year} {curr_events[0]}; cosa vuoi fare?"
            else:
                return (
                    handler_input.response_builder
                        .speak("Non ho trovato altri eventi!")
                        .response
                )
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output) 
                .response
        )    

class RetrieveEventHandler(AbstractRequestHandler):
    """Handler for Skill Launch and RetrieveEvent Intent."""
    
    def can_handle(self, handler_input):
        return is_intent_name("RetrieveEvents")(handler_input)

    def handle(self, handler_input):

        event_date_str = get_slot_value(handler_input=handler_input, slot_name="date")

        event_date = datetime.strptime(event_date_str, "%Y-%m-%d")
        event_day = f"{event_date.month}-{event_date.day}"

        persistence_attributes = handler_input.attributes_manager.persistent_attributes

        events = persistence_attributes.get(event_day, {})

        speak_out = f"Mi spiace. Non è successo niente il {event_date.strftime('%d %B')}"
        if events:
            speak_out = " ".join([f"Nel {year} {'; '.join(events[year])}." for year in sorted(events)])

        return (
            handler_input.response_builder
                .speak(speak_out)
                .response
        )
        
        
class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In HelpIntentHandler")

        # get localization data
        data = handler_input.attributes_manager.request_attributes["_"]

        speech = data[prompts.HELP_MESSAGE]
        reprompt = data[prompts.HELP_REPROMPT]
        handler_input.response_builder.speak(speech).ask(
            reprompt).set_card(SimpleCard(
                data[prompts.SKILL_NAME], speech))
        return handler_input.response_builder.response


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In CancelOrStopIntentHandler")

        # get localization data
        data = handler_input.attributes_manager.request_attributes["_"]

        speech = data[prompts.STOP_MESSAGE]
        handler_input.response_builder.speak(speech)
        return handler_input.response_builder.response


class FallbackIntentHandler(AbstractRequestHandler):
    """Handler for Fallback Intent.

    AMAZON.FallbackIntent is only available in en-US locale.
    This handler will not be triggered except in that locale,
    so it is safe to deploy on any locale.
    """

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")

        # get localization data
        data = handler_input.attributes_manager.request_attributes["_"]

        speech = data[prompts.FALLBACK_MESSAGE]
        reprompt = data[prompts.FALLBACK_REPROMPT]
        handler_input.response_builder.speak(speech).ask(
            reprompt)
        return handler_input.response_builder.response


class LocalizationInterceptor(AbstractRequestInterceptor):
    """
    Add function to request attributes, that can load locale specific data.
    """

    def process(self, handler_input):
        locale = handler_input.request_envelope.request.locale
        logger.info("Locale is {}".format(locale))

        # localized strings stored in language_strings.json
        with open("language_strings.json") as language_prompts:
            language_data = json.load(language_prompts)
        # set default translation data to broader translation
        if locale[:2] in language_data:
            data = language_data[locale[:2]]
            # if a more specialized translation exists, then select it instead
            # example: "fr-CA" will pick "fr" translations first, but if "fr-CA" translation exists,
            # then pick that instead
            if locale in language_data:
                data.update(language_data[locale])
        else:
            data = language_data[locale]
        handler_input.attributes_manager.request_attributes["_"] = data


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In SessionEndedRequestHandler")

        logger.info("Session ended reason: {}".format(
            handler_input.request_envelope.request.reason))
        return handler_input.response_builder.response


# Exception Handler
class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Catch all exception handler, log exception and
    respond with custom message.
    """

    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.info("In CatchAllExceptionHandler")
        logger.error(exception, exc_info=True)

        handler_input.response_builder.speak(ERROR_MESSAGE).ask(
            HELP_REPROMPT)

        return handler_input.response_builder.response


# Request and Response loggers
class RequestLogger(AbstractRequestInterceptor):
    """Log the alexa requests."""

    def process(self, handler_input):
        # type: (HandlerInput) -> None
        logger.debug("Alexa Request: {}".format(
            handler_input.request_envelope.request))


class ResponseLogger(AbstractResponseInterceptor):
    """Log the alexa responses."""

    def process(self, handler_input, response):
        # type: (HandlerInput, Response) -> None
        logger.debug("Alexa Response: {}".format(response))

sb = CustomSkillBuilder(persistence_adapter = dynamodb_adapter)

# Register intent handlers
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(GetTimeToHomeHandler())
sb.add_request_handler(AddEventRequestHandler())
sb.add_request_handler(AddEventTypeHandler())
sb.add_request_handler(RetrieveEventHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(ModifyEventsRequestHandler())
sb.add_request_handler(DeleteEventHandler())
sb.add_request_handler(NextEventHandler())

# Register exception handlers
sb.add_exception_handler(CatchAllExceptionHandler())

# Register request and response interceptors
sb.add_global_request_interceptor(LocalizationInterceptor())
sb.add_global_request_interceptor(RequestLogger())
sb.add_global_response_interceptor(ResponseLogger())

# Handler name that is used on AWS lambda
lambda_handler = sb.lambda_handler()
