# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.
# Hobknob is the cli tool for using and managing the Hob appllication server
# from the command line. It provides a simple interface to the Hob API.


from hobknob.commands import cli_handler


@cli_handler("auth", subcommand="login", description="Login to Hob")
def auth_login_handler(args):
    """Log in to the system."""
    print(f"Logging in with username: {args.username} and password: {args.password}")


# Configure arguments directly in the function
def configure_auth_login(parser):
    parser.add_argument("--username", required=True, help="Your username")
    parser.add_argument("--password", required=True, help="Your password")


auth_login_handler.configure_parser = configure_auth_login


@cli_handler("auth", subcommand="logout", description="Logout from Hob")
def auth_logout_handler(args):
    """Log out of the system."""
    print("Logging out...")
