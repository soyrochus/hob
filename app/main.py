# Copyright © 2025, MIT License, Author: Iwan van der Kleijn 
# Hob: A private AI-augmented workspace for project notes and files.

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt

from .models import BundleResponse
from pydantic import BaseModel, EmailStr

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

fake_users_db = {
    "johndoe@example.com": {
        "name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "fakehashedsecret",  # In reality, store hashed passwords
        "age": 30
    }
}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Token(BaseModel):
    access_token: str
    token_type: str


class UserRegistration(BaseModel):
    name: str
    email: EmailStr
    age: int
    password: str


class TokenData(BaseModel):
    email: Optional[str] = None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def authenticate_user(email: str, password: str):
    user = fake_users_db.get(email)
    if not user:
        return None
    # This is a demo. Normally you'd verify the password here.
    if password != "secret": # A real system would hash and check
        return None
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = fake_users_db.get(token_data.email)
    if user is None:
        raise credentials_exception
    return user


@app.post("/register", status_code=201)
async def register_user(user: UserRegistration):
    logger.info(f"Register attempt: {user.email}")
    if user.email in fake_users_db:
        raise HTTPException(status_code=400, detail="Email already registered")
    fake_users_db[user.email] = {
        "name": user.name,
        "email": user.email,
        "hashed_password": "fakehashed" + user.password,
        "age": user.age
    }
    return {"status": "success"}


@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    logger.info(f"Login attempt: {form_data.username}")
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        logger.warning("Invalid credentials")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"]}, expires_delta=access_token_expires
    )
    logger.info("Login successful")
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/bundles", response_model=List[BundleResponse])
async def list_bundles(current_user: dict = Depends(get_current_user)):
    logger.info("GET /bundles request")
    # Return mock data
    return [
        BundleResponse(
            id="bundle-1",
            name="Project Alpha",
            description="Notes and files",
            created_at=datetime.utcnow()
        ),
        BundleResponse(
            id="bundle-2",
            name="Meeting Notes",
            description="Q4 Sales Meeting",
            created_at=datetime.utcnow()
        )
    ]
