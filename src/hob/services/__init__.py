# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.


from hob.config.provider_types import LLM
from typing import cast


class ServiceManager:
    _services = {}  # type: ignore

    @classmethod
    def register(cls, name, service):
        cls._services[name] = service

    @classmethod
    def get(cls, name) -> object:
        return cls._services[name]

    @classmethod
    def get_llm(cls) -> LLM:
        return cast(LLM, cls.get("llm"))
