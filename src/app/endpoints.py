# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.


import logging
from datetime import timedelta
from typing import List
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

# Local imports
from app.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    get_current_user,
)
from hob.data.api import get_user_bundles
from hob.data.db import get_db_session
from hob.services import ServiceManager
from .schemas import BundleResponse, ChatResponse, UserData, Token

logger = logging.getLogger(__name__)


def create_app(lifespan_func):
    """
    Define the ASGI application.
    """

    app = FastAPI(lifespan=lifespan_func)

    # CORS configuration
    # For a production environment, you should specify the allowed origins
    # app.add_middleware(
    #     CORSMiddleware,
    #     allow_origins=["https://your-frontend-domain.com"],
    #     allow_credentials=True,
    #     allow_methods=["GET", "POST"],
    #     allow_headers=["Authorization", "Content-Type"],
    # )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.post("/token", response_model=Token)
    async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        session: AsyncSession = Depends(get_db_session),
    ):
        logger.info(f"Login attempt: {form_data.username}")
        user = await authenticate_user(session, form_data.username, form_data.password)
        if not user:
            logger.warning("Invalid credentials")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        logger.info("Login successful")
        return {"access_token": access_token, "token_type": "bearer"}

    @app.get("/bundles", response_model=List[BundleResponse])
    async def list_bundles(
        current_user: UserData = Depends(get_current_user),
        session: AsyncSession = Depends(get_db_session),
    ):
        logger.info("GET /bundles request")

        # bundles = await db.scalars(select(Bundle))
        bundles = await get_user_bundles(session, current_user.id)
        return [
            BundleResponse(
                id=b.id, name=b.name, description=b.description, created_at=b.created_at
            )
            for b in bundles
        ]

    @app.get("/")
    async def root():
        return {"message": "Hob is running"}

    @app.get("/chat", response_model=List[ChatResponse])
    async def chat(current_user: UserData = Depends(get_current_user)):
        message = await ServiceManager.get_llm().send(
            f"Hello, I am {current_user.name}, who are you?"
        )
        return [ChatResponse(message=message)]

    return app
