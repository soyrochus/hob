# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.

from datetime import timedelta, datetime
from typing import Optional
from fastapi import Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession


# Local imports

from hob.data.api import get_user_by_email, get_user_by_login
from hob.auth import validate_password
from hob.data.db import get_db_session
from .schemas import UserData


import logging

logger = logging.getLogger(__name__)

# SECRET_KEY = "supersecretkey"
SECRET_KEY = "3414cf1c7a01c020976330890a3d161d"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def authenticate_user(session: AsyncSession, username: str, password: str):
    user = await get_user_by_login(session, username)
    if not user:
        return None

    if validate_password(password, user.password):
        return user
    else:
        None


async def get_current_user(
    response: Response,
    session: AsyncSession = Depends(get_db_session),
    token: str = Depends(oauth2_scheme),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub")
        if email is None:
            raise credentials_exception

        # Check token expiration
        exp = datetime.utcfromtimestamp(payload["exp"])
        current_time = datetime.utcnow()
        trigger_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES * 0.8)
        # Refresh the token if used but ignoring frequent repeated use
        # during the first 20% of its lifetime
        if current_time > (exp - trigger_delta):
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": email}, expires_delta=access_token_expires
            )
            response.headers["Authorization"] = f"Bearer {access_token}"

    except JWTError:
        raise credentials_exception

    user = await get_user_by_email(session, email)
    if user is None:
        raise credentials_exception

    return UserData(id=user.id, login=user.login, name=user.name, email=user.email)  # type: ignore
