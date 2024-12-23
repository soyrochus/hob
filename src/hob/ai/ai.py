# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.

from typing import Protocol
from langchain_openai.chat_models.base import ChatOpenAI

# local import
from hob.config import ConfigurationManager


class LLM(Protocol):
    async def send(self, prompt: str) -> str:
        ...


class OpenAILLM(LLM):
    def __init__(self, config: ConfigurationManager):

        # Initialize the OpenAI chat model with the asynchronous interface
        self.llm = ChatOpenAI(
            model=config.get("openai", "model"),
            openai_api_key=config.get("openai", "api_key")
        ) 

    async def send(self, prompt: str) -> str:
        # Send the prompt using the asynchronous OpenAI chat model
        return await self.llm.ainvoke(prompt)
