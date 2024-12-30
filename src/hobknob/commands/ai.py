# Copyright © 2025, MIT License, Author: Iwan van der Kleijn
# Hob: A private AI-augmented workspace for project notes and files.
# Hobknob is the cli tool for using and managing the Hob appllication server
# from the command line. It provides a simple interface to the Hob API.

from hobknob.client import get_client
from hobknob.commands import cli_handler
from hobknob.commands.bundles import SELECTED_BUNDLE_KEY
from hobknob.config import get_config


@cli_handler(
    "chat",
    subcommand="single",
    description="Single interaction with LLM model in Bundle",
)
async def chat_single_handler(args):
    """Select a specific bundle."""

    config = get_config()
    client = get_client()

    set_bundle_id = config.read_state().get(SELECTED_BUNDLE_KEY, None)
    bundle_id = args.bundle or set_bundle_id
    if not bundle_id:
        print(
            "Please provide a bundle ID, either as an argument or by selecting a bundle with 'bundles select'"
        )
        return

    data = {"bundle_id": bundle_id, "message": args.prompt, "conversation_id": None}

    # data = ChatRequest(bundle_id=bundle_id, message=args.prompt)
    # response = await client.post_async("/chat", data=data, response_model=ChatResponse)
    print("Message:", end=" ")
    async for s in client.stream_post("/stream", data=data):
        print(s, end="")

    # print(f"Bundle ID: {response.bundle_id}")
    # print(f"Message: {response.message}")


def configure_chat_single(parser):
    parser.add_argument("prompt", type=str, help="The prompt to send to the AI")
    parser.add_argument(
        "--bundle",
        type=int,
        default=None,
        help="The ID of the bundle to select (optional)",
    )


chat_single_handler.configure_parser = configure_chat_single
