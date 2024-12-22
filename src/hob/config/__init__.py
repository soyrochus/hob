# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.

import tomllib
from typing import Any

SYSTEM = "system"


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
