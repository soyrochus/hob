# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.

import pytest
from hob.auth import hash_password
from hob.config import ConfigurationManager as Config
from hob.data.db import get_db_engine, get_async_session_local, init_db, Base
from hob.data.models import Artifact, Bundle, User, user_bundle
from hob.data.api import get_user_bundles, get_user_by_login
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
async def db_session():
    Config.load("./tests/hob-test-config.toml")

    init_db()

    # Initialize the database engine
    engine = get_db_engine()

    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

    # Create a session for testing
    session = get_async_session_local()

    yield session  # Provide the session to the test


@pytest.mark.asyncio
async def test_get_user_bundle(db_session) -> None:
    async with db_session as session:
        await initialize_bundles(session)

        user = await get_user_by_login(session, "test")
        assert user.name == "Test User"

        bundles = await get_user_bundles(session, user.id)
        assert len(bundles) == 2
        assert bundles[0].name == "Hob Project"


async def initialize_bundles(session: AsyncSession):  # type: ignore
    """
    Populates the database with mock data: a user, two bundles, and artifacts.
    """
    # Create the user
    user = User(
        login="test",
        name="Test User",
        email="test@example.com",
        password=hash_password("meep"),  # Hash the password
    )
    session.add(user)

    # Flush to get the auto-generated user ID
    await session.flush()
    user_id = user.id

    # # Create bundles
    bundle1 = Bundle(name="Hob Project")
    bundle2 = Bundle(name="Personal")
    session.add_all([bundle1, bundle2])

    # # Flush to get the auto-generated bundle IDs
    await session.flush()
    bundle1_id = bundle1.id
    bundle2_id = bundle2.id

    # Create artifacts
    artifact1 = Artifact(
        name="Prompt Template", type="text", origin="Stored in DB", bundle_id=bundle1_id
    )
    artifact2 = Artifact(
        name="Personal Text", type="text", origin="Stored in DB", bundle_id=bundle2_id
    )
    session.add_all([artifact1, artifact2])

    # Flush to save artifacts
    await session.flush()

    # Link user to bundles (user_bundle table)
    await session.execute(
        user_bundle.insert().values(user_id=user_id, bundle_id=bundle1_id)
    )
    await session.execute(
        user_bundle.insert().values(user_id=user_id, bundle_id=bundle2_id)
    )
    await session.flush()
