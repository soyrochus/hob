# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.


from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from .models import Bundle, user_bundle


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


async def get_user_bundles(session: AsyncSession, user_id: str):
    """
    Fetch all bundles associated with a user.
    """
    result = await session.execute(
        select(Bundle)
        .join(user_bundle, user_bundle.c.bundle_id == Bundle.id)
        .where(user_bundle.c.user_id == user_id)
        .options(joinedload(Bundle.users))
    )
    return result.scalars().all()
