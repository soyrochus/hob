# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.
# Hobknob is the cli tool for using and managing the Hob appllication server
# from the command line. It provides a simple interface to the Hob API.


import argparse
from typing import Callable, Dict, Optional, Any

from hobknob.client import get_client

# Command registry
COMMAND_HANDLERS: Dict[str, Callable] = {}
SUBCOMMAND_HANDLERS: Dict[str, Dict[str, Callable]] = {}


def verify_auth(auth_required: bool):
    if auth_required:
        if get_client().get_jwt_token() is None:
            raise Exception(
                "Authentication required. Use 'hobknob auth login' to authenticate."
            )
    else:
        pass  # No auth required


def cli_handler(
    command: str,
    subcommand: Optional[str] = None,
    description: Optional[str] = None,
    auth_required: Optional[bool] = True,
):
    """
    Decorator to register a handler for a command or subcommand.

    :param command: The primary command name (e.g., 'auth').
    :param subcommand: The subcommand name (e.g., 'login'). If None, this is a top-level command.
    :param description: The description for the command or subcommand.
    """

    def decorator(func: Callable):
        if subcommand:
            SUBCOMMAND_HANDLERS.setdefault(command, {})[subcommand] = {  # type: ignore
                "handler": func,
                "description": description,
                "auth_required": auth_required,
            }
        else:
            COMMAND_HANDLERS[command] = {  # type: ignore
                "handler": func,
                "description": description,
                "auth_required": auth_required,
            }
        return func

    return decorator


async def parse_and_execute(
    program_name: str, program_description: str, global_parser: Any, init_global: Any
):  # type: ignore
    """
    Parse command-line arguments and execute the appropriate handler.
    """
    parser = argparse.ArgumentParser(prog=program_name, description=program_description)

    await global_parser(parser)

    subparsers = parser.add_subparsers(
        dest="command", required=True, help="Available commands"
    )

    # Add top-level commands and subcommands
    for command, command_meta in COMMAND_HANDLERS.items():
        cmd_parser = subparsers.add_parser(command, help=command_meta["description"])  # type: ignore
        if hasattr(command_meta["handler"], "configure_parser"):  # type: ignore
            command_meta["handler"].configure_parser(cmd_parser)  # type: ignore

    for command, subcommands in SUBCOMMAND_HANDLERS.items():
        cmd_parser = subparsers.add_parser(command, help=f"{command} commands")
        sub_subparsers = cmd_parser.add_subparsers(
            dest="subcommand", required=True, help=f"{command} subcommands"
        )
        for subcommand, subcommand_meta in subcommands.items():
            sub_cmd_parser = sub_subparsers.add_parser(
                subcommand,
                help=subcommand_meta["description"],  # type: ignore
            )
            if hasattr(subcommand_meta["handler"], "configure_parser"):  # type: ignore
                subcommand_meta["handler"].configure_parser(sub_cmd_parser)  # type: ignore

    # Parse arguments
    args = parser.parse_args()

    # execute the global handler(s)
    await init_global(args)

    # Execute the appropriate handler
    if args.command in COMMAND_HANDLERS:
        handler = COMMAND_HANDLERS[args.command]["handler"]  # type: ignore
        auth_required = COMMAND_HANDLERS[args.command]["auth_required"]  # type: ignore
        verify_auth(auth_required)
        await handler(args)
    elif args.command in SUBCOMMAND_HANDLERS and args.subcommand:
        handler = SUBCOMMAND_HANDLERS[args.command][args.subcommand]["handler"]  # type: ignore
        auth_required = SUBCOMMAND_HANDLERS[args.command][args.subcommand][
            "auth_required"
        ]  # type: ignore
        verify_auth(auth_required)
        await handler(args)
    else:
        parser.error("Invalid command or subcommand")
