# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.


import pytest
from hob.config import ConfigurationManager as Config
from hob.services import ServiceManager


@pytest.fixture
async def service_man():
    Config.load("./tests/hob-test-config.toml")
    Config.initialize_services()

    yield ServiceManager


@pytest.mark.asyncio
async def test_llm(service_man):
    llm = service_man.get_llm()
    assert await llm.send("Hello") == "This is a mock response"
