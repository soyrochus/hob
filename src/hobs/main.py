# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.
# Hobs is the API service for Hob. It provides a simple interface to the Hob API.

import argparse
import logging
import os
from fastapi import FastAPI
import uvicorn

# Local imports
from hobs.endpoints import create_app
from hob.config import ConfigurationManager as Config
from hob.data.db import init_db, Base, get_db_engine


def parse_arguments():
    """
    Parse command-line arguments to get the configuration file path.
    """
    parser = argparse.ArgumentParser(description="Run the Hob application server.")

    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default="hob-config.toml",
        help="Path to the TOML configuration file (default: hob-config.toml)",
    )
    parser.add_argument(
        "--host", type=str, default="127.0.0.1", help="Host to bind the server."
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port to bind the server."
    )
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload.")
    parser.add_argument("--log-level", type=str, default="info", help="Logging level.")

    # Parse known and unknown args
    args, unknown_args = parser.parse_known_args()

    # Prepare uvicorn kwargs
    uvicorn_kwargs = {
        "host": args.host,
        "port": args.port,
        "reload": args.reload,
        "log_level": args.log_level,
    }

    print(f"Starting server with: {uvicorn_kwargs}")
    print(f"Unknown parameters passed to uvicorn: {unknown_args}")

    # Allow unknown arguments to pass through (used by uvicorn)

    return args, uvicorn_kwargs, unknown_args


def initialize_config(config_path: str):
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


# FastAPI application expects an app variable in the global scope
app = None  # Ensure app is a global variable


def create_app_once():
    global app
    if app is None:  # Initialize app only once
        config_path = os.environ.get("HOB_APP_CONFIG_PATH")
        initialize_config(config_path)
        app = create_app(lifespan)
    return app


def main():

    args, uvicorn_kwargs, _ = parse_arguments()
    # Set the config path in an environment variable
    os.environ["HOB_APP_CONFIG_PATH"] = args.config

    create_app_once()
    # Run uvicorn
    uvicorn.run("hobs.main:create_app_once", factory=True, **uvicorn_kwargs)


if __name__ == "__main__":
    main()
