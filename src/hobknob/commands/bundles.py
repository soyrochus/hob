# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.
# Hobknob is the cli tool for using and managing the Hob appllication server
# from the command line. It provides a simple interface to the Hob API.

from hobknob.client import get_client
from hobknob.commands import cli_handler
from hobknob.config import get_config
from hobknob.schemas import BundleResponse

SELECTED_BUNDLE_KEY = "selected_bundle"


@cli_handler("bundles", subcommand="list", description="Display available bundles")
async def bundles_list_handler(args):
    """Display available bundles"""

    client = get_client()
    response = await client.get_async("/bundles", response_model=BundleResponse)

    if len(response) > 0:
        for bundle in response:
            print(f"{bundle.id} - {bundle.name}")
            if args.verbose:
                print(f" Description:   {bundle.description}")
                print(f" Created at:    {bundle.created_at}")
    else:
        print("No bundles found")


def configure_bundles_list(parser):
    parser.add_argument("--verbose", action="store_true", help="Show detailed info")


bundles_list_handler.configure_parser = configure_bundles_list


@cli_handler("bundles", subcommand="select", description="Select a bundle")
async def bundles_select_handler(args):
    """Select a specific bundle."""

    config = get_config()
    client = get_client()
    response = await client.get_async("/bundles", response_model=BundleResponse)

    # see if there is a bundle with the given ID
    for bundle in response:
        if bundle.id == args.id:
            config.update_state({SELECTED_BUNDLE_KEY: bundle.id})
            print(f"Bundle selected: {bundle.id} - {bundle.name}")
            return

    print(f"No bundle found with ID {args.id}")


def configure_bundles_select(parser):
    parser.add_argument("id", type=int, help="The ID of the bundle to select")


bundles_select_handler.configure_parser = configure_bundles_select
