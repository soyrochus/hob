# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.
# Hobknob is the cli tool for using and managing the Hob appllication server
# from the command line. It provides a simple interface to the Hob API.


from httpx import HTTPStatusError
from hobknob.client import get_client
from hobknob.commands import cli_handler
from hobknob.config import get_config
from hobknob.schemas import Token

TOKEN_KEY = "token"


@cli_handler(
    "auth", subcommand="login", description="Login to Hob", auth_required=False
)
async def auth_login_handler(args):
    """Log in to the system."""
    user_name = args.username
    password = args.password

    data = {
        "username": user_name,
        "password": password,
    }

    client = get_client()
    try:
        response = await client.post_async(
            "/token", data=data, form_data=True, response_model=Token
        )
        config = get_config()
        config.update_state({TOKEN_KEY: response.access_token})
        print("Logged in successfully.")
    except HTTPStatusError as e:
        if e.response.status_code == 401:
            print("Invalid credentials. Please try again.")
            exit(1)
        else:
            raise e


@cli_handler(
    "auth", subcommand="logout", description="Logout from Hob", auth_required=False
)
async def auth_logout_handler(args):
    """Log out of the system."""
    reset_auth()
  
    print("Logout successful.")


def reset_auth():
    config = get_config()
    config.remove_state(TOKEN_KEY)

# Configure arguments directly in the function
def configure_auth_login(parser):
    parser.add_argument("--username", required=True, help="Your username")
    parser.add_argument("--password", required=True, help="Your password")


auth_login_handler.configure_parser = configure_auth_login
