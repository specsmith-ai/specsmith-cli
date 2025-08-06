#!/usr/bin/env python3
"""Example usage of the SpecSmith CLI."""

import asyncio
import os

from specsmith_cli.chat import run_chat
from specsmith_cli.config import load_config


async def example_chat():
    """Example of using the chat interface programmatically."""

    # Set up configuration
    config = load_config(
        api_url="http://localhost:8000",
        access_key_id="your-access-key-id",
        access_key_token="your-access-key-token",
    )

    # Send a single message
    await run_chat(
        config,
        message="Create a Python function to calculate fibonacci numbers",
        interactive=False,
    )


if __name__ == "__main__":
    # This is just an example - you would need real credentials
    print(
        "This is an example script showing how to use the SpecSmith CLI programmatically."
    )
    print("To use it, you need to:")
    print("1. Set up your API credentials")
    print("2. Replace the placeholder credentials with real ones")
    print("3. Ensure the SpecSmith API is running")

    # Uncomment the following lines to run the example:
    # asyncio.run(example_chat())
