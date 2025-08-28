"""Main CLI entry point for Specsmith."""

import asyncio
import sys
from typing import Optional

import click
from rich.console import Console

from .api_client import SpecSmithAPIClient
from .chat import run_chat
from .config import (
    Config,
    load_config,
    setup_credentials_interactive,
    validate_credentials,
)

console = Console()
# Start chat session


def _start_chat(ctx: click.Context) -> None:
    if ctx.obj["config"] is None:
        console.print(
            f"[red]❌ Configuration error: {ctx.obj.get('config_error')}[/red]"
        )
        sys.exit(1)

    # Validate credentials
    if not validate_credentials(ctx.obj["config"]):
        console.print("[red]❌ Invalid API credentials format[/red]")
        sys.exit(1)
    # Run the chat
    try:
        asyncio.run(run_chat(ctx.obj["config"]))
    except KeyboardInterrupt:
        console.print("\n[yellow]Goodbye![/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)


@click.group(invoke_without_command=True)
@click.option(
    "--api-url",
    envvar="SPECSMITH_API_URL",
    default="https://api.specsmith.ai",
    help="Specsmith API URL",
)
@click.option(
    "--access-key-id",
    envvar="SPECSMITH_ACCESS_KEY_ID",
    help="Specsmith Access Key ID",
)
@click.option(
    "--access-key-token",
    envvar="SPECSMITH_ACCESS_KEY_TOKEN",
    help="Specsmith Access Key Token",
)
@click.option(
    "--debug",
    is_flag=True,
    envvar="SPECSMITH_DEBUG",
    help="Enable debug mode",
)
@click.pass_context
def main(
    ctx: click.Context,
    api_url: str,
    access_key_id: Optional[str],
    access_key_token: Optional[str],
    debug: bool,
) -> None:
    """Specsmith CLI - Start a chat session with Specsmith AI."""
    ctx.ensure_object(dict)

    # Store raw options for commands that don't need full config
    ctx.obj["raw_options"] = {
        "api_url": api_url,
        "access_key_id": access_key_id,
        "access_key_token": access_key_token,
        "debug": debug,
    }

    # Try to load config, but don't fail if credentials are missing
    try:
        config = load_config(
            api_url=api_url,
            access_key_id=access_key_id,
            access_key_token=access_key_token,
            debug=debug,
        )
        ctx.obj["config"] = config
    except ValueError as e:
        # Only store error for commands that need config
        ctx.obj["config_error"] = str(e)
        ctx.obj["config"] = None

    # If no subcommand was invoked, start chat
    if ctx.invoked_subcommand is None:
        _start_chat(ctx)


@main.command()
@click.pass_context
def chat(ctx: click.Context) -> None:
    """Start a chat session with Specsmith (same as running 'specsmith' without arguments)."""
    _start_chat(ctx)


@main.command()
@click.pass_context
def setup(ctx: click.Context) -> None:
    """Set up API credentials interactively."""
    console.print("[bold blue]Specsmith CLI Setup[/bold blue]")
    console.print()
    console.print("This will help you configure your API credentials.")
    console.print("You can get your API keys from the Specsmith web interface.")
    console.print()

    setup_credentials_interactive()


@main.command()
@click.pass_context
def test(ctx: click.Context) -> None:
    """Test the connection to the Specsmith API."""
    config: Config = ctx.obj.get("config")

    if config is None:
        console.print(
            f"[red]❌ Configuration error: {ctx.obj.get('config_error')}[/red]"
        )
        sys.exit(1)

    console.print("[blue]Testing connection to Specsmith API...[/blue]")

    async def test_connection():
        async with SpecSmithAPIClient(config) as client:
            if await client.test_connection():
                console.print("[green]✅ Connection successful![/green]")
                console.print(f"API URL: {config.api_url}")
                console.print("Your credentials are working correctly.")
            else:
                console.print("[red]❌ Connection failed[/red]")
                console.print("Please check:")
                console.print("1. The API is running")
                console.print("2. Your API credentials are correct")
                console.print("3. The API URL is correct")
                sys.exit(1)

    try:
        asyncio.run(test_connection())
    except Exception as e:
        console.print(f"[red]❌ Test failed: {e}[/red]")
        sys.exit(1)


@main.command()
@click.pass_context
def config(ctx: click.Context) -> None:
    """Show current configuration."""
    config: Config = ctx.obj.get("config")

    if config is None:
        console.print(
            f"[red]❌ Configuration error: {ctx.obj.get('config_error')}[/red]"
        )
        sys.exit(1)

    console.print("[bold blue]Current Configuration[/bold blue]")
    console.print(f"API URL: {config.api_url}")
    console.print(f"Access Key ID: {config.access_key_id[:8]}...")
    console.print(f"Debug Mode: {config.debug}")


@main.command()
def version() -> None:
    """Show version information."""
    from . import __version__

    console.print(f"Specsmith CLI v{__version__}")


if __name__ == "__main__":
    main()
