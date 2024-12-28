# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.
# Hobknob is the cli tool for using and managing the Hob appllication server
# from the command line. It provides a simple interface to the Hob API.


from hobknob.commands import cli_handler


@cli_handler("bundles", subcommand="select", description="Select a bundle")
def bundles_select_handler(args):
    """Select a specific bundle."""
    print(f"Bundle selected: {args.id}")


def configure_bundles_select(parser):
    parser.add_argument("id", type=int, help="The ID of the bundle to select")


bundles_select_handler.configure_parser = configure_bundles_select


@cli_handler("bundles", subcommand="info", description="Display current bundle status")
def bundles_info_handler(args):
    """Display current bundle status."""
    print(f"Bundle status: Active bundle (verbose={args.verbose})")


def configure_bundles_info(parser):
    parser.add_argument("--verbose", action="store_true", help="Show detailed info")


bundles_info_handler.configure_parser = configure_bundles_info
