# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.
# Hobknob is the cli tool for using and managing the Hob appllication server
# from the command line. It provides a simple interface to the Hob API.


import asyncio
from hobknob.client import ClientType, HTTPClient, set_client
from hobknob.commands import parse_and_execute
import hobknob.commands.bundles  # noqa:
import hobknob.commands.auth  # noqa:
import hobknob.commands.info  # noqa:

from hobknob.config import FileBasedConfigState, set_config

APP_NAME = "hobknob"
APP_DESCRIPTION = "Hobknob is the CLI tool for using and managing the Hob application server from the command line."
DEFAULT_URL = "http://localhost:8000"


async def global_parser(parser):
    parser.add_argument(
        "--config",
        default=None,
        help="Path to the configuration file.",
    )
    parser.add_argument(
        "--state",
        default=None,
        help="Path to the state file.",
    )

    return parser


async def init_global(args):

    if args.config:
        config_file = args.config
    else:
        config_file = None

    if args.state:
        state_file = args.state
    else:
        state_file = None

    config = FileBasedConfigState(
        APP_NAME, config_file=config_file, state_file=state_file
    )
    set_config(config)

    config_data = config.read_config()
    url = config_data.get("url", DEFAULT_URL)

    client = HTTPClient(url, mode=ClientType.Asynchronous, config=config)

    state_data = config.read_state()
    token = state_data.get("token", None)
    if token:
        client.set_jwt_token(token)

    set_client(client)


async def async_main():
    try:
        await parse_and_execute(
            program_name=APP_NAME,
            program_description=APP_DESCRIPTION,
            global_parser=global_parser,
            init_global=init_global,
        )

    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    asyncio.run(async_main())
