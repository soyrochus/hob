# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.

import tomllib
from typing import Any
from hob.config import openai
from hob.config.mock_provider import MockInitializer
from hob.exceptions import ConfigurationError
from hob.services import ServiceManager

SYSTEM = "system"


PROVIDERS = {
    "mock": MockInitializer,
    "openai": openai.Initializer
}


class ConfigurationManager:
    _config: dict[str, Any] = {}

    @classmethod
    def load(cls, config_path):
        """
        Load the configuration from a TOML file.
        """
        with open(config_path, "rb") as f:
            cls._config = tomllib.load(f)

    @classmethod
    def get(cls, section, key, default=None):
        """
        Retrieve a value from the configuration.
        """
        return cls._config.get(section, {}).get(key, default)

    @classmethod
    def initialize_services(cls):
        """
        Initialize all configurable providers.
        """
        ai_provider = cls.get(SYSTEM, "ai-provider")
        if ai_provider in PROVIDERS:
            PROVIDERS[ai_provider].initialize(cls, ServiceManager)
        else:
            raise ConfigurationError(f"Unknown AI provider: {ai_provider}")
