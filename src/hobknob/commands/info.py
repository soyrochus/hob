# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.
# Hobknob is the cli tool for using and managing the Hob appllication server
# from the command line. It provides a simple interface to the Hob API.

from hobknob.client import get_client
from hobknob.commands import cli_handler
from hobknob.schemas import Response


@cli_handler(
    "info",
    subcommand="ping",
    description="Check if server is running",
    auth_required=False,
)
async def info_ping_handler(args):
    """Check to see if server is running"""

    client = get_client()
    try:
        response = await client.get_async("/", response_model=Response)
        if response.message == "Hob is running":
            print(f"Server is running on {client.base_url}")
        else:
            print(f"Unexpected response from server on {client.base_url}")

    except Exception as e:
        print(f"Error: {e}")
        print(f"Server on {client.base_url} is not reachable or is not running")
