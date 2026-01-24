# -*- coding: utf-8 -*-
"""
Rigotti Home Alexa Skill - Entry Point

This module configures and exports the Lambda handler for the Alexa skill.
All handler implementations are in the handlers/ package.
"""

import logging
import os

import boto3
from ask_sdk_core.skill_builder import CustomSkillBuilder
from ask_sdk_dynamodb.adapter import DynamoDbAdapter

# Handler imports
from handlers import (
    LaunchRequestHandler,
    AddEventRequestHandler,
    AddEventTypeHandler,
    AddEventCompleteHandler,
    RetrieveEventHandler,
    ModifyEventsRequestHandler,
    NextEventHandler,
    PreviousEventHandler,
    DeleteEventHandler,
    ConfirmDeleteHandler,
    CancelDeleteHandler,
    EditEventHandler,
    EditEventDescriptionHandler,
    HelpIntentHandler,
    CancelOrStopIntentHandler,
    FallbackIntentHandler,
    SessionEndedRequestHandler,
)
from interceptors import (
    LocalizationInterceptor,
    RequestLogger,
    ResponseLogger,
)
from exceptions import CatchAllExceptionHandler

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# DynamoDB configuration
ddb_region = os.environ.get('DYNAMODB_PERSISTENCE_REGION', 'eu-west-1')
ddb_table_name = os.environ['DYNAMODB_PERSISTENCE_TABLE_NAME']

ddb_resource = boto3.resource('dynamodb', region_name=ddb_region)
dynamodb_adapter = DynamoDbAdapter(
    table_name=ddb_table_name,
    create_table=False,
    dynamodb_resource=ddb_resource
)

# Build skill
sb = CustomSkillBuilder(persistence_adapter=dynamodb_adapter)

# Register request handlers (order matters for can_handle evaluation)
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(AddEventRequestHandler())
sb.add_request_handler(AddEventTypeHandler())
sb.add_request_handler(AddEventCompleteHandler())
sb.add_request_handler(RetrieveEventHandler())
sb.add_request_handler(ModifyEventsRequestHandler())
sb.add_request_handler(NextEventHandler())
sb.add_request_handler(PreviousEventHandler())
sb.add_request_handler(DeleteEventHandler())
sb.add_request_handler(ConfirmDeleteHandler())
sb.add_request_handler(CancelDeleteHandler())
sb.add_request_handler(EditEventHandler())
sb.add_request_handler(EditEventDescriptionHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

# Register exception handlers
sb.add_exception_handler(CatchAllExceptionHandler())

# Register interceptors
sb.add_global_request_interceptor(LocalizationInterceptor())
sb.add_global_request_interceptor(RequestLogger())
sb.add_global_response_interceptor(ResponseLogger())

# Export Lambda handler
lambda_handler = sb.lambda_handler()
