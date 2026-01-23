"""Localization interceptor for loading language-specific strings."""

import json
import logging
from pathlib import Path

from ask_sdk_core.dispatch_components import AbstractRequestInterceptor
from ask_sdk_core.handler_input import HandlerInput

logger = logging.getLogger(__name__)

# Path to language strings file (relative to lambda directory)
LANGUAGE_STRINGS_PATH = Path(__file__).parent.parent / "language_strings.json"


class LocalizationInterceptor(AbstractRequestInterceptor):
    """
    Add localized strings to request attributes.

    Loads locale-specific data from language_strings.json and makes it
    available via handler_input.attributes_manager.request_attributes["_"]
    """

    def __init__(self) -> None:
        self._language_data: dict = {}
        self._load_language_data()

    def _load_language_data(self) -> None:
        """Load language strings from JSON file."""
        try:
            with open(LANGUAGE_STRINGS_PATH, encoding="utf-8") as f:
                self._language_data = json.load(f)
        except FileNotFoundError:
            logger.error(f"Language strings file not found: {LANGUAGE_STRINGS_PATH}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in language strings file: {e}")

    def process(self, handler_input: HandlerInput) -> None:
        locale = handler_input.request_envelope.request.locale
        logger.info(f"Locale is {locale}")

        # Get base language (e.g., "it" from "it-IT")
        base_locale = locale[:2] if locale else "en"

        # Start with base translation
        data = {}
        if base_locale in self._language_data:
            data = self._language_data[base_locale].copy()

        # Override with locale-specific translation if available
        if locale in self._language_data:
            data.update(self._language_data[locale])

        # Fallback to English if no data found
        if not data and "en" in self._language_data:
            data = self._language_data["en"].copy()
            logger.warning(f"No translation for locale {locale}, falling back to English")

        handler_input.attributes_manager.request_attributes["_"] = data
