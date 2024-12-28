# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.
# Hobknob is the cli tool for using and managing the Hob appllication server
# from the command line. It provides a simple interface to the Hob API.


from typing import List
from hobknob.client import get_client
from hobknob.commands import cli_handler
from hobknob.schemas import BundleResponse

@cli_handler("bundles", subcommand="list", description="Display available bundles")
async def bundles_list_handler(args):
    """Display available bundles"""
    
    client = get_client()
    response = await client.get_async("/bundles", response_model=BundleResponse)
    
    if response:
        if len(response) == 0:
            print("No bundles found")
            return
        for bundle in response:
            print(f"{bundle.id}: {bundle.name}")
            if args.verbose:
                print(f"  Description: {bundle.description}")
                print(f"  Created at: {bundle.created_at}")
        
    else:
        print("Unexpected response from server")
    

def configure_bundles_list(parser):
    parser.add_argument("--verbose", action="store_true", help="Show detailed info")


bundles_list_handler.configure_parser = configure_bundles_list


@cli_handler("bundles", subcommand="select", description="Select a bundle")
async def bundles_select_handler(args):
    """Select a specific bundle."""
    print(f"Bundle selected: {args.id}")


def configure_bundles_select(parser):
    parser.add_argument("id", type=int, help="The ID of the bundle to select")


bundles_select_handler.configure_parser = configure_bundles_select



