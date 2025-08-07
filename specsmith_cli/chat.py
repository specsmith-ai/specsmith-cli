"""Chat interface for the Specsmith CLI."""

import asyncio
import os
from pathlib import Path
from typing import Any, Dict, Optional, List

from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.patch_stdout import patch_stdout
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm
from rich.spinner import Spinner
from rich.text import Text

from .api_client import SpecSmithAPIClient
from .config import Config
from .errors import SpecsmithError, get_user_friendly_message


class ChatInterface:
    """Interactive chat interface for Specsmith CLI."""

    def __init__(self, config: Config):
        self.config = config
        self.console = Console()
        self.session_id: Optional[str] = None
        self.api_client: Optional[SpecSmithAPIClient] = None
        self.pending_file_saves: List[Dict[str, Any]] = []

        # Initialize prompt-toolkit session with custom key bindings
        self.prompt_session = PromptSession()
        self.kb = KeyBindings()

        @self.kb.add("enter")
        def _(event):
            buffer = event.app.current_buffer
            if buffer.document.text.endswith("\n"):
                # Submit on double enter
                buffer.validate_and_handle()
            else:
                buffer.insert_text("\n")

        @self.kb.add("c-j")  # Ctrl+J for enter
        def _(event):
            buffer = event.app.current_buffer
            buffer.validate_and_handle()

    async def start(self, initial_message: Optional[str] = None) -> None:
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

            # Send initial message if provided
            if initial_message:
                await self._send_message(initial_message)
            else:
                self.console.print("\n[bold blue]Specsmith Chat[/bold blue]")
                self.console.print("Type your message or 'quit' to exit.\n")

            # Start interactive loop
            await self._interactive_loop()

        except (KeyboardInterrupt, EOFError):
            # Handle Ctrl+C and Ctrl+D gracefully
            self.console.print("\n[yellow]Goodbye![/yellow]")
        except SpecsmithError as e:
            # Display user-friendly error message
            message = get_user_friendly_message(e)
            self.console.print(f"[red]{message}[/red]")
        except Exception as e:
            # Handle any other exceptions with sanitized messages
            from .errors import create_error_from_exception

            error = create_error_from_exception(e, self.config.debug)
            message = get_user_friendly_message(error)
            self.console.print(f"[red]{message}[/red]")
        finally:
            if self.api_client:
                await self.api_client.aclose()

    async def _interactive_loop(self) -> None:
        """Main interactive chat loop."""
        while True:
            try:
                # Get user input using prompt-toolkit
                self.console.print("\n[bold cyan]You[/bold cyan]")
                with patch_stdout():
                    message = await self.prompt_session.prompt_async(
                        ">>> ", multiline=True, key_bindings=self.kb
                    )

                if message.lower() in ("quit", "exit", "q"):
                    self.console.print("[yellow]Goodbye![/yellow]")
                    break

                if not message.strip():
                    continue

                # Send message and handle response
                await self._send_message(message)

            except (KeyboardInterrupt, EOFError):
                # Handle Ctrl+C and Ctrl+D gracefully
                self.console.print("\n[yellow]Goodbye![/yellow]")
                break
            except SpecsmithError as e:
                # Display user-friendly error message
                message = get_user_friendly_message(e)
                self.console.print(f"[red]{message}[/red]")
            except Exception as e:
                # Handle any other exceptions with sanitized messages
                from .errors import create_error_from_exception

                error = create_error_from_exception(e, self.config.debug)
                message = get_user_friendly_message(error)
                self.console.print(f"[red]{message}[/red]")

    async def _send_message(self, message: str) -> None:
        """Send a message and handle the streaming response."""
        if not self.api_client or not self.session_id:
            raise ValueError("API client or session not initialized")

        try:
            # Print Specsmith header
            self.console.print("\n[bold blue]Specsmith:[/bold blue]")

            # Start with empty content for streaming
            current_content = ""

            # Create initial markdown for streaming updates
            md = Markdown("")

            # Use Live display for streaming updates without panel borders
            with Live(md, refresh_per_second=4, console=self.console) as live:
                # Show spinner while waiting for first response
                spinner = Spinner("dots")
                live.update(spinner)

                async for action in self.api_client.send_message(
                    self.session_id, message
                ):
                    if action.get("type") == "message":
                        content = action.get("content", "")
                        if content:
                            current_content += content
                            # Update the markdown content directly
                            md = Markdown(current_content)
                            live.update(md)
                    else:
                        # Handle non-message actions
                        await self._handle_action(action)

            # Final check if we have content
            if not current_content or not current_content.strip():
                self.console.print("[dim]No response received[/dim]")
            else:
                # Add a newline after the panel for better formatting
                self.console.print()

            # Process any pending file saves
            await self._process_pending_file_saves()

        except SpecsmithError as e:
            # Display user-friendly error message
            message = get_user_friendly_message(e)
            self.console.print(f"[red]{message}[/red]")
        except Exception as e:
            # Handle any other exceptions with sanitized messages
            from .errors import create_error_from_exception

            error = create_error_from_exception(e, self.config.debug)
            message = get_user_friendly_message(error)
            self.console.print(f"[red]{message}[/red]")

    async def _handle_action(self, action: Dict[str, Any]) -> None:
        """Handle different types of actions from the API."""
        action_type = action.get("type")

        if action_type == "message":
            # Content is handled in _send_message for streaming
            pass

        elif action_type == "file":
            await self._handle_file_action(action)

        elif action_type == "user_action":
            await self._handle_user_action(action)

        else:
            # Unknown action type, just print it
            if self.config.debug:
                self.console.print(f"[yellow]Unknown action type: {action}[/yellow]")

    async def _handle_user_action(self, action: Dict[str, Any]) -> None:
        """Handle user actions from tool call results."""
        action_data = action.get("action", {})
        action_type = action_data.get("type")

        if self.config.debug:
            self.console.print(
                f"[yellow]DEBUG: Received user_action: {action}[/yellow]"
            )
            self.console.print(f"[yellow]DEBUG: action_data: {action_data}[/yellow]")
            self.console.print(f"[yellow]DEBUG: action_type: {action_type}[/yellow]")

        if action_type == "file_saved":
            # Handle file save action - collect for later processing
            file_name = action_data.get("file_name", "")
            content = action_data.get("content", "")
            operation = action_data.get("operation", "saved")
            spec_id = action_data.get("spec_id", "")

            if self.config.debug:
                self.console.print(f"[yellow]DEBUG: file_name: {file_name}[/yellow]")
                self.console.print(
                    f"[yellow]DEBUG: content length: {len(content) if content else 0}[/yellow]"
                )
                self.console.print(f"[yellow]DEBUG: operation: {operation}[/yellow]")
                self.console.print(f"[yellow]DEBUG: spec_id: {spec_id}[/yellow]")

            # Display success message
            self.console.print(
                f"\n[green]✅ Specification {operation} successfully![/green]"
            )
            self.console.print(f"  • File Name: {file_name}")
            if spec_id:
                self.console.print(f"  • Specification ID: {spec_id}")

            # Collect file save for later processing
            if file_name and content:
                self.pending_file_saves.append(
                    {"filename": file_name, "content": content}
                )
            else:
                if self.config.debug:
                    self.console.print(
                        f"[yellow]DEBUG: Skipping file save - missing file_name or content[/yellow]"
                    )

        elif action_type == "tag_created":
            tag_value = action_data.get("tag_value", "")
            tag_id = action_data.get("tag_id", "")
            created_at = action_data.get("created_at", "")

            self.console.print(f"\n[green]✅ Tag created successfully![/green]")
            self.console.print(f"  • Tag Value: {tag_value}")
            if tag_id:
                self.console.print(f"  • Tag ID: {tag_id}")
            if created_at:
                self.console.print(f"  • Created at: {created_at}")

        elif action_type == "error":
            tool_name = action_data.get("tool", "unknown")
            message = action_data.get("message", "An error occurred")

            self.console.print(f"\n[red]❌ Error in {tool_name}: {message}[/red]")

        else:
            # Unknown user action type, print it in debug mode
            if self.config.debug:
                self.console.print(
                    f"[yellow]Unknown user action type: {action_type}[/yellow]"
                )
                self.console.print(f"[yellow]Action data: {action_data}[/yellow]")

    def _handle_file_save(self, filename: str, content: str) -> None:
        """Handle file save action with user prompts."""
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

        except (KeyboardInterrupt, EOFError):
            # Handle Ctrl+C and Ctrl+D gracefully
            self.console.print("\n[yellow]Goodbye![/yellow]")
        except SpecsmithError as e:
            # Display user-friendly error message
            message = get_user_friendly_message(e)
            self.console.print(f"[red]{message}[/red]")
        except Exception as e:
            # Handle any other exceptions with sanitized messages
            from .errors import create_error_from_exception

            error = create_error_from_exception(e, self.config.debug)
            message = get_user_friendly_message(error)
            self.console.print(f"[red]{message}[/red]")
        finally:
            if self.api_client:
                await self.api_client.aclose()

    async def _process_pending_file_saves(self) -> None:
        """Process any pending file saves after streaming is complete."""
        if not self.pending_file_saves:
            return

        self.console.print("\n[blue]📁 File Save Options:[/blue]")

        for file_save in self.pending_file_saves:
            filename = file_save["filename"]
            content = file_save["content"]

            # Handle file save with user prompts
            self._handle_file_save(filename, content)

        # Clear the pending list
        self.pending_file_saves.clear()


async def run_chat(
    config: Config,
    message: Optional[str] = None,
    interactive: bool = True,
) -> None:
    """Run the chat interface."""
    chat = ChatInterface(config)

    if interactive:
        await chat.start(message)
    else:
        if not message:
            raise ValueError("Message is required for non-interactive mode")
        await chat.send_single_message(message)
