# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.

import pytest
from hob.config import ConfigurationManager as Config
from hob.db import get_db_engine, get_async_session_local, init_db, Base
from hob.services import get_user_bundles


@pytest.fixture
async def db_session():  # type: ignore
    
    Config.load('./tests/hob-test-config.toml')
    
    # Initialize the database
    init_db()
    async with get_db_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session = get_async_session_local()
    yield session
  

data1 = "A simple text"
data2 = "Another simple text"


@pytest.mark.asyncio
async def test_get_user_bundle(db_session) -> None:
    
    async with db_session as session:
        
        assert await get_user_bundles(session, 'test_user') == []

 