# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.

from hob.services import ServiceManager


class MockLLM:
    def __init__(self, config):
        self.response = config.get("mock", "response")

    async def send(self, prompt: str) -> str:
        return self.response


class MockInitializer:
    @staticmethod
    def initialize(config, service_man: ServiceManager):
        # Initialize the Mock LLM
        mock_llm = MockLLM(config)
        service_man.register("llm", mock_llm)