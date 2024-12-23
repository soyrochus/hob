# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.


from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from .models import Bundle, User, user_bundle


# # Create a new User
# async def create_user(session: AsyncSession, name: str, email: str):
#     user = User(id=name.lower(), name=name, email=email)
#     session.add(user)
#     await session.commit()
#     return user


# # Create a new Bundle
# async def create_bundle(session: AsyncSession, name: str, owner_id=None, group_id=None):
#     bundle = Bundle(id=name.lower(), name=name, owner_id=owner_id, group_id=group_id)
#     session.add(bundle)
#     await session.commit()
#     return bundle


async def get_user_bundles(session: AsyncSession, user_id: int):
    """
    Fetch all bundles associated with a user.
    """
    result = await session.execute(
        select(Bundle)
        .distinct()  # Ensure unique results
        .join(user_bundle, user_bundle.c.bundle_id == Bundle.id)
        .where(user_bundle.c.user_id == user_id)
        .options(joinedload(Bundle.users))
    )
    return result.unique().scalars().all()


async def get_user_by_login(session: AsyncSession, user_name: str) -> User | None:
    """
    Fetch a User by their login / username from the database.

    Args:
        session (AsyncSession): The database session.
        user_name (str): The login/user name of the user to fetch.

    Returns:
        User | None: The User instance if found, or None otherwise.
    """
    result = await session.execute(select(User).where(User.login == user_name))
    user = result.scalar_one_or_none()  # Fetch one result or return None
    return user


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """
    Fetch a User by their email from the database.

    Args:
        session (AsyncSession): The database session.
        email (str): The email address of the user to fetch.

    Returns:
        User | None: The User instance if found, or None otherwise.
    """
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()  # Fetch one result or return None
    return user
