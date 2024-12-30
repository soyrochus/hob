# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.

from typing import AsyncGenerator, Protocol


class LLM(Protocol):
    async def send(self, prompt: str) -> str: ...

    async def stream(self, prompt: str) -> AsyncGenerator[str, None]: ...
