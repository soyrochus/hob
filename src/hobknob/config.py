# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.
# Hobknob is the cli tool for using and managing the Hob appllication server
# from the command line. It provides a simple interface to the Hob API.


from pathlib import Path
from typing import Optional, Protocol
import os
import yaml
import tomllib


class ConfigStateInterface(Protocol):
    """
    Protocol defining the interface for configuration and state management.
    """

    def read_config(self) -> dict:
        """
        Read the configuration file and return it as a dictionary.
        """
        ...

    def read_state(self) -> dict:
        """
        Read the state file and return it as a dictionary.
        """
        ...

    def write_state(self, state: dict) -> None:
        """
        Write the given state to the state file.
        """
        ...


class FileBasedConfigState(ConfigStateInterface):
    """
    File-based implementation of the ConfigStateInterface.
    """

    def __init__(
        self,
        app_name: str,
        config_file: Optional[str] = None,
        state_file: Optional[str] = None,
    ):
        self._app_name = app_name

        home_directory = Path.home() / f".{app_name}"
        os.makedirs(home_directory, exist_ok=True)

        if config_file:
            self._config_file = Path(config_file)
            self._custom_config_file = True
        else:
            self._config_file = home_directory / "{app_name}-config.toml"
            self._custom_config_file = False

        if state_file:
            self._state_file = Path(state_file)
        else:
            self._state_file = (
                home_directory / f"{app_name}-state.dta"
            )  # Use .dta ext but it's a yaml file

    def read_config(self) -> dict:
        """
        Reads the YAML configuration file and returns it as a dictionary.
        """
        if not os.path.exists(self._config_file):

            if self._custom_config_file:
                raise FileNotFoundError(f"Config file not found: {self._config_file}")
            else:
                return {}
        else:
            with open(self._config_file, "rb") as f:
                return tomllib.load(f)

    def read_state(self) -> dict:
        """
        Reads the YAML state file and returns it as a dictionary.
        """
        if not os.path.exists(self._state_file):
            return {}  # Default to an empty state if the file doesn't exist

        with open(self._state_file, "r") as f:
            return yaml.safe_load(f)

    def write_state(self, state: dict) -> None:
        """
        Writes the given state to the YAML state file.
        """
        with open(self._state_file, "w") as f:
            yaml.safe_dump(state, f)


_config: Optional[ConfigStateInterface] = None


def get_config() -> ConfigStateInterface:
    global _config
    if _config is None:
        raise RuntimeError("Configuration has not been set.")
    return _config


def set_config(config: ConfigStateInterface):
    global _config
    _config = config
