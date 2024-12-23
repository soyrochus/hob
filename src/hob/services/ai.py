# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.


from hob.config.provider_types import LLM
from hob.services import ServiceManager


async def llm_send(prompt: str) -> str:
    """
    Send a prompt to the OpenAI Language Model API.
    """
    llm: LLM = ServiceManager.get_llm()
    return await llm.send(prompt)