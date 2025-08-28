"""Chat interface for the Specsmith CLI."""

from pathlib import Path
from typing import Any, Dict, Optional

from rich.console import Console
from rich.prompt import Confirm, Prompt

from .api_client import SpecSmithAPIClient
from .config import Config


class ChatInterface:
    """Interactive chat interface for Specsmith CLI."""

    def __init__(self, config: Config):
        self.config = config
        self.console = Console()
        self.session_id: Optional[str] = None
        self.api_client: Optional[SpecSmithAPIClient] = None

    async def start(self) -> None:
        """Start the chat interface."""
        try:
            # Initialize API client
            self.api_client = SpecSmithAPIClient(self.config)

            # Test connection
            self.console.print("[blue]Testing connection to Specsmith API...[/blue]")
            if not await self.api_client.test_connection():
                self.console.print("[red]❌ Failed to connect to Specsmith API[/red]")
                self.console.print("Please check:")
                self.console.print("1. The API is running")
                self.console.print("2. Your API credentials are correct")
                self.console.print("3. The API URL is correct")
                return

            self.console.print("[green]✅ Connected to Specsmith API[/green]")

            # Create session for chat
            self.session_id = await self.api_client.create_session()

            # Show welcome message
            self.console.print("\n[bold blue]Specsmith Chat[/bold blue]")
            self.console.print("Type your message or 'quit' to exit.\n")

            # Start interactive loop
            await self._interactive_loop()

        except Exception as e:
            self.console.print(f"[red]❌ Error: {e}[/red]")
        finally:
            if self.api_client:
                await self.api_client.aclose()

    async def _interactive_loop(self) -> None:
        """Main interactive chat loop."""
        while True:
            try:
                # Get user input
                message = Prompt.ask("\n[bold cyan]You[/bold cyan]")

                if message.lower() in ("quit", "exit", "q"):
                    self.console.print("[yellow]Goodbye![/yellow]")
                    break

                if not message.strip():
                    continue

                # Send message and handle response
                await self._send_message(message)

            except KeyboardInterrupt:
                self.console.print("\n[yellow]Goodbye![/yellow]")
                break
            except Exception as e:
                self.console.print(f"[red]❌ Error: {e}[/red]")

    async def _send_message(self, message: str) -> None:
        """Send a message and handle the streaming response."""
        if not self.api_client or not self.session_id:
            raise ValueError("API client or session not initialized")

        try:
            async for action in self.api_client.send_message(self.session_id, message):
                if action.get("type") == "message":
                    content = action.get("content", "")
                    if content:
                        # Print content immediately without newlines unless they exist in the text
                        self.console.print(content, end="", markup=False)
                else:
                    # Handle non-message actions
                    await self._handle_action(action)

        except Exception as e:
            self.console.print(f"[red]❌ Error sending message: {e}[/red]")

    async def _handle_action(self, action: Dict[str, Any]) -> None:
        """Handle different types of actions from the API."""
        action_type = action.get("type")

        if action_type == "message":
            # Content is handled in _send_message for streaming
            pass

        elif action_type == "file":
            await self._handle_file_action(action)
        elif action_type == "tool_use":
            # Print whisper for tool use
            description = action.get("description") or action.get("tool_name", "tool")
            self.console.print(f"[dim]( {description} )…[/dim]")
        elif action_type == "limit_message":
            # Print limit message as whisper without ellipses
            content = action.get("content", "")
            if content:
                self.console.print(f"[dim]{content}[/dim]")

        else:
            # Unknown action type, just print it
            if self.config.debug:
                self.console.print(f"[yellow]Unknown action type: {action}[/yellow]")

    async def _handle_file_action(self, action: Dict[str, Any]) -> None:
        """Handle file actions with user prompts."""
        filename = action.get("filename", "")
        content = action.get("content", "")

        if not filename or not content:
            return

        file_path = Path(filename)

        # Check if file exists
        if file_path.exists():
            # File exists, ask for overwrite
            overwrite = Confirm.ask(
                f"File '{filename}' already exists. Do you want to overwrite it?",
                default=False,
            )
            if not overwrite:
                self.console.print(f"[yellow]Skipped saving {filename}[/yellow]")
                return
        else:
            # File doesn't exist, ask for save
            save = Confirm.ask(f"Save file '{filename}'?", default=True)
            if not save:
                self.console.print(f"[yellow]Skipped saving {filename}[/yellow]")
                return

        # Save the file
        try:
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w") as f:
                f.write(content)

            self.console.print(f"[green]✅ Saved {filename}[/green]")

        except Exception as e:
            self.console.print(f"[red]❌ Failed to save {filename}: {e}[/red]")

    async def send_single_message(self, message: str) -> None:
        """Send a single message and exit."""
        try:
            # Initialize API client
            self.api_client = SpecSmithAPIClient(self.config)

            # Create session
            self.session_id = await self.api_client.create_session()

            # Send message and handle response
            await self._send_message(message)

        except Exception as e:
            self.console.print(f"[red]❌ Error: {e}[/red]")
        finally:
            if self.api_client:
                await self.api_client.aclose()


async def run_chat(config: Config) -> None:
    """Run the interactive chat interface."""
    chat = ChatInterface(config)
    await chat.start()
