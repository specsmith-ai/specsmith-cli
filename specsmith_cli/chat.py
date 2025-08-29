"""Chat interface for the Specsmith CLI."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

from .api_client import SpecSmithAPIClient
from .config import Config


class ChatInterface:
    """Interactive chat interface for Specsmith CLI."""

    def __init__(self, config: Config):
        self.config = config
        self.console = Console()
        self.session_id: Optional[str] = None
        self.api_client: Optional[SpecSmithAPIClient] = None
        self.current_directory = os.getcwd()
        self.project_name = Path(self.current_directory).name

        # Create prompt session with custom key bindings
        self.prompt_session = self._create_prompt_session()

        # Style for the interface
        self.style = Style.from_dict(
            {
                "border": "#888888",
                "title": "#00aaff bold",
                "subtitle": "#888888",
                "prompt": "#00aaff bold",
                "input-box": "#ffffff bg:#1e1e1e",
                "help-text": "#888888",
                "workspace": "#ffaa00",
            }
        )

    def _create_prompt_session(self) -> PromptSession:
        """Create a prompt session with line continuation support using backslash."""
        kb = KeyBindings()

        @kb.add("c-c")
        def _(event):
            """Exit on Ctrl+C."""
            event.app.exit(exception=KeyboardInterrupt)

        return PromptSession(
            key_bindings=kb,
            multiline=False,  # We'll handle multiline manually
            wrap_lines=True,
        )

    def _show_welcome_screen(self) -> None:
        """Display the Claude Code-style welcome screen with panels."""
        # Clear screen
        os.system("clear" if os.name == "posix" else "cls")

        # Welcome panel with Specsmith brand colors
        welcome_panel = Panel(
            "[#D4A63D]✻ Welcome to Specsmith Agent![/]\n\n  How can I help you today?\n  I can help you create, refine, and manage software specifications.\n\n  [dim]cwd: "
            + self.current_directory
            + "[/dim]",
            title=None,
            border_style="#6AA9FF",  # Blueprint Wash blue
            padding=(1, 2),
        )
        self.console.print(welcome_panel)
        self.console.print()

    async def start(self) -> None:
        """Start the chat interface."""
        try:
            # Initialize API client
            self.api_client = SpecSmithAPIClient(self.config)

            # Test connection
            self.console.print("[dim]Testing connection to Specsmith API...[/dim]")
            if not await self.api_client.test_connection():
                self.console.print("[red]❌ Failed to connect to Specsmith API[/red]")
                self.console.print(
                    "Please check that your API credentials are correct."
                )
                self.console.print("You can update them by running: specsmith setup")
                return

            self.console.print("[green]✅ Connected to Specsmith API[/green]")

            # Create session for chat
            self.session_id = await self.api_client.create_session()

            # Show welcome screen after connection is established
            self._show_welcome_screen()

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
                # Get user input with line continuation support
                message = await self._get_multiline_input()

                if message.lower().strip() in ("quit", "exit", "q"):
                    self.console.print("[dim]Goodbye![/dim]")
                    break

                if not message.strip():
                    continue

                # Show the user's message in a panel
                self._show_user_message(message)

                # Send message and handle response
                await self._send_message(message)

            except KeyboardInterrupt:
                self.console.print("\n[dim]Goodbye![/dim]")
                break
            except EOFError:
                # Ctrl+D pressed
                self.console.print("\n[dim]Goodbye![/dim]")
                break
            except Exception as e:
                self.console.print(f"[red]❌ Error: {e}[/red]")

    async def _get_multiline_input(self) -> str:
        """Get user input with backslash line continuation support."""
        # Show a simple prompt before input
        self.console.print()

        lines = []
        first_line = True

        while True:
            if first_line:
                prompt = HTML("<ansibrightblack>> </ansibrightblack>")
                first_line = False
            else:
                prompt = HTML("<ansibrightblack>  \\ </ansibrightblack>")

            try:
                line = await self.prompt_session.prompt_async(prompt, style=self.style)
            except EOFError:
                # Ctrl+D pressed - propagate the EOFError to be handled by the main loop
                raise

            # Strip any trailing whitespace first
            line = line.rstrip()

            if line.endswith("\\"):
                # Line continuation - remove backslash and any trailing whitespace
                clean_line = line[:-1].rstrip()
                lines.append(clean_line)
            else:
                # End of input - add the line as-is
                lines.append(line)
                break

        return "\n".join(lines)

    def _show_user_message(self, message: str) -> None:
        """Display the user's message in a panel."""
        user_panel = Panel(
            message,
            title=None,
            border_style="bright_black",
            padding=(0, 1),
            title_align="left",
        )
        self.console.print()
        self.console.print(user_panel)

    async def _send_message(self, message: str) -> None:
        """Send a message and handle the streaming response."""
        if not self.api_client or not self.session_id:
            raise ValueError("API client or session not initialized")

        try:
            # Show agent indicator (bright dot)
            self.console.print()
            self.console.print("● ", end="", style="bright_white")

            async for action in self.api_client.send_message(self.session_id, message):
                if action.get("type") == "message":
                    content = action.get("content", "")
                    if content:
                        # Print content with full brightness, no markup
                        self.console.print(
                            content, end="", markup=False, style="bright_white"
                        )
                else:
                    # Handle non-message actions
                    await self._handle_action(action)

            # Add newline after response
            self.console.print()

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
            # Print whisper for tool use in dim style
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
