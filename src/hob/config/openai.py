# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.


from typing import AsyncGenerator
from langchain_openai import ChatOpenAI
from hob.config.provider_types import LLM
from hob.services import ServiceManager


class Initializer:
    @staticmethod
    def initialize(config, service_man: ServiceManager):
        # Initialize the OpenAI LLM
        openai_llm = OpenAILLM(config)
        service_man.register("llm", openai_llm)


class OpenAILLM(LLM):
    def __init__(self, config):

        # Initialize the OpenAI chat model with the asynchronous interface
        self.llm = ChatOpenAI(
            model=config.get("openai", "model"),
            openai_api_key=config.get("openai", "api-key"),
        )

    async def send(self, prompt: str) -> str:
        # Send the prompt using the asynchronous OpenAI chat model
        response = await self.llm.ainvoke(prompt)
        return response.content

    async def stream(self, prompt: str) -> AsyncGenerator[str, None]:    # type: ignore
        # Send the prompt using the streaming OpenAI chat model
        # Stream the response asynchronously
        # return self.llm.astream(prompt)
        
        async for response in self.llm.astream(prompt):   # type: ignore
            
            data = response.content
            yield data  # type: ignore
            
            
