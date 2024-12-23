# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.

import argparse
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

# Local imports
from hob.config import ConfigurationManager as Config
from hob.data.api import get_user_bundles, get_user_by_email, get_user_by_login
from hob.data.db import init_db, Base, get_db_engine, get_db_session
from hob.auth import validate_password
from hob.services import ServiceManager
from .schemas import BundleResponse, ChatResponse, UserData



def parse_arguments():
    """
    Parse command-line arguments to get the configuration file path.
    """
    parser = argparse.ArgumentParser(description="Run the application server.")
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default="hob-config.toml",
        help="Path to the TOML configuration file (default: hob-config.toml)",
    )
    # Allow unknown arguments to pass through (used by uvicorn)
    args, unknown = parser.parse_known_args()
    return args


def initialize_config(config_path="hob-config.toml"):
    """
    Initialize the application with the given configuration.
    """
    Config.load(config_path)

    # Initialize all configurable services
    Config.initialize_services()

    # Initialize the database
    init_db()

    print(f"Application initialized with config: {config_path}")


# Set up logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SECRET_KEY = "supersecretkey"
SECRET_KEY = "3414cf1c7a01c020976330890a3d161d"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Lifespan context manager
async def lifespan(app: FastAPI):
    # Startup tasks (database initialization)
    async with get_db_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Yield control to the application
    yield

    # Shutdown tasks (if any)
    # You can add cleanup logic here
    pass


class Token(BaseModel):
    access_token: str
    token_type: str
    

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


async def get_current_user(session: AsyncSession = Depends(get_db_session), 
                           token: str = Depends(oauth2_scheme)):
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
        
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_email(session, email)
    if user is None:
        raise credentials_exception
    
    return UserData(id=user.id, login=user.login, name=user.name, email=user.email)


# Uvicorn expects an `app` variable in this module
def create_app():
    """
    Define the ASGI application.
    """

    args = parse_arguments()
    initialize_config(args.config)

    app = FastAPI(lifespan=lifespan)

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
    async def login(form_data: OAuth2PasswordRequestForm = Depends(), 
                    session: AsyncSession = Depends(get_db_session)):
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
    async def chat(
        current_user: UserData = Depends(get_current_user)
    ):
        message = await ServiceManager.get_llm().send(f"Hello, I am {current_user.name}, who are you?")
        return [ChatResponse(message=message)]
    
    return app

app = create_app()
