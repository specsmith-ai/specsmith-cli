"""Chat interface for the Specsmith Agent."""

import os
from typing import Any, Dict, Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.spinner import Spinner
from rich.text import Text

from .api_client import SpecSmithAPIClient
from .config import Config
from .utils import handle_file_action


class ChatInterface:
    """Interactive chat interface for Specsmith CLI."""

    def __init__(self, config: Config):
        self.config = config
        self.console = Console()
        self.session_id: Optional[str] = None
        self.api_client: Optional[SpecSmithAPIClient] = None

        # Track if we've shown the welcome message
        self.welcome_shown = False
        self.supports_shift_enter = os.environ.get("TERM_PROGRAM", "").lower() in (
            "vscode",
            "cursor",
        )
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

        # Check if we're in a terminal that supports Shift+Enter (like VSCode/Cursor)
        # For terminals that don't support Shift+Enter, add Ctrl+K as continuation trigger
        if not self.supports_shift_enter:

            @kb.add("c-k")
            def _(event):
                """Add backslash continuation for multiline input in terminals without Shift+Enter support."""
                event.current_buffer.insert_text("\\")
                event.current_buffer.validate_and_handle()

        return PromptSession(
            key_bindings=kb,
            multiline=False,  # We'll handle multiline manually with backslash continuation
            wrap_lines=True,
        )

    def _normalize_markdown_alignment(self, content: str) -> str:
        """Normalize excessive left-padding outside fenced code blocks for better rendering.

        Keeps fenced code blocks verbatim; preserves proper markdown indentation;
        only removes excessive leading spaces that would cause unintended code blocks.
        """
        lines = content.splitlines()
        normalized: list[str] = []
        in_code = False

        for line in lines:
            rline = line.rstrip()
            lstripped = rline.lstrip()

            # Handle fenced code blocks
            if lstripped.startswith("```"):
                in_code = not in_code
                normalized.append(rline)
                continue

            # Preserve content inside fenced code blocks
            if in_code:
                normalized.append(rline)
                continue

            # For non-code content, be more careful about preserving markdown structure
            leading_spaces = len(rline) - len(lstripped)

            # Preserve proper markdown indentation (2-3 spaces for nested lists, blockquotes)
            if leading_spaces <= 3:
                normalized.append(rline)
            # Only strip when we have excessive indentation (4+ spaces) that would trigger code blocks
            elif leading_spaces >= 4:
                # Check if this might be intentional indentation for nested elements
                if lstripped.startswith(("-", "*", "+")) and leading_spaces <= 6:
                    # Preserve reasonable list indentation (up to 6 spaces)
                    normalized.append(rline)
                elif lstripped.startswith(">") and leading_spaces <= 6:
                    # Preserve reasonable blockquote indentation
                    normalized.append(rline)
                else:
                    # Strip excessive indentation that would cause code blocks
                    normalized.append(lstripped)
            else:
                normalized.append(rline)

        return "\n".join(normalized)

    def _show_welcome_message(self) -> None:
        """Show the welcome message if not already shown."""
        if not self.welcome_shown:
            welcome_panel = Panel(
                "[#D4A63D]* Welcome to Specsmith Agent![/]\n\n  [bold]How can I help you today?[/bold]\n\n  [italic]I can help you create, refine, and manage software specifications.[/italic]",
                title=None,
                border_style="#6AA9FF",
                padding=(1, 2),
            )
            self.console.print(welcome_panel)
            self.console.print()  # Add spacing after welcome

            # Show input instructions once
            if self.supports_shift_enter:
                self.console.print(" • Press [bold]Shift+Enter[/bold] for a new line")
            else:
                self.console.print(" • Press [bold]Ctrl+K[/bold] for a new line")
            self.console.print(" • Press [bold]Enter[/bold] to submit your message")
            self.console.print(
                " • Type [italic]quit[/italic] or press [bold]Ctrl+C[/bold] / [bold]Ctrl+D[/bold] to exit"
            )
            self.console.print()

            self.welcome_shown = True

    def _show_welcome_screen(self) -> None:
        """Display the welcome screen."""
        # Clear screen
        os.system("clear" if os.name == "posix" else "cls")

        # Show welcome message
        self._show_welcome_message()

    async def start(self) -> None:
        """Start the chat interface."""
        try:
            # Initialize API client
            self.api_client = SpecSmithAPIClient(self.config)

            # Test connection
            self.console.print("[dim]Connecting to Specsmith API...[/dim]")
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
                # Show welcome message if this is the first interaction
                self._show_welcome_message()

                # Get user input with line continuation support
                message = await self._get_multiline_input()

                if message.lower().strip() in ("quit", "exit", "q"):
                    self.console.print("[dim]Goodbye![/dim]")
                    break

                if not message.strip():
                    continue

                # Show the user's message
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
        lines_entered = 0  # Track how many lines we've processed

        while True:
            if first_line:
                prompt = HTML("<ansibrightblack>> </ansibrightblack>")
                first_line = False
            else:
                # Use invisible prompt - just spaces for positioning
                prompt = HTML("  ")

            try:
                line = await self.prompt_session.prompt_async(prompt, style=self.style)
                lines_entered += 1
            except EOFError:
                # Ctrl+D pressed - propagate the EOFError to be handled by the main loop
                raise

            # Strip any trailing whitespace first
            line = line.rstrip()

            if line.endswith("\\"):
                # Line continuation - remove backslash and any trailing whitespace
                clean_line = line[:-1].rstrip()
                lines.append(clean_line)

                # Clear the line that shows the backslash, replace with clean version
                try:
                    stream = self.console.file
                    stream.write("\x1b[1A\r\x1b[K")  # Clear the line with backslash
                    stream.flush()
                except Exception:
                    pass

                # Show the clean line without backslash
                if len(lines) == 1:  # First line
                    self.console.print(f"> {clean_line}")
                else:  # Continuation lines
                    self.console.print(f"  {clean_line}")
            else:
                # End of input - add the line as-is
                lines.append(line)
                break

        # Clear all the input lines we've shown
        try:
            stream = self.console.file
            for _ in range(lines_entered):
                stream.write("\x1b[1A\r\x1b[K")
            stream.flush()
        except Exception:
            pass

        return "\n".join(lines)

    def _show_user_message(self, message: str) -> None:
        """Display the user's message in a panel, prefixed with '> ' on first line."""
        # Prefix first line with "> " and indent subsequent lines for readability
        lines = message.splitlines() or [""]
        prefixed_lines = [("> " + lines[0]) if lines else "> "]
        for ln in lines[1:]:
            prefixed_lines.append("  " + ln)

        user_panel = Panel(
            Text("\n".join(prefixed_lines), style="dim"),
            title=None,
            border_style="bright_black",
            padding=(0, 1),
            title_align="left",
        )
        self.console.print(user_panel)
        # And exactly one blank line after the user panel before assistant output
        self.console.print()

    async def _send_message(self, message: str) -> None:
        """Send a message and stream the response using Rich Live panel."""
        if not self.api_client or not self.session_id:
            raise ValueError("API client or session not initialized")

        try:
            response_text = ""
            first_content_received = False
            pending_file_actions = []

            # Ensure a blank line precedes assistant output for consistent spacing
            self.console.print()

            # Start with spinner while waiting for first response
            spinner = Spinner("dots", text="[dim]Thinking...[/dim]")

            with Live(spinner, refresh_per_second=10, console=self.console) as live:
                async for action in self.api_client.send_message(
                    self.session_id, message
                ):
                    if action.get("type") == "message":
                        content = action.get("content", "")
                        if content:
                            # Switch from spinner to markdown on first content
                            if not first_content_received:
                                first_content_received = True
                                live.update(Markdown(""))

                            response_text += content
                            # Apply markdown normalization before rendering
                            normalized_text = self._normalize_markdown_alignment(
                                response_text
                            )
                            live.update(Markdown(normalized_text))
                    elif action.get("type") == "file":
                        # Defer file actions to avoid prompt conflicts with Live display
                        pending_file_actions.append(action)
                    else:
                        # Handle other actions immediately (tool_use, limit_message, etc.)
                        await self._handle_action(action)

            # Handle file actions after Live context ends to allow prompts to display
            for action in pending_file_actions:
                await self._handle_file_action(action)

            # One trailing blank line after assistant output to separate from next turn
            self.console.print()

        except Exception as e:
            self.console.print(f"[red]❌ Error: {e}[/red]")

    async def _handle_action(self, action: Dict[str, Any]) -> None:
        """Handle different types of actions from the API."""
        action_type = action.get("type")

        if self.config.debug:
            self.console.print(
                f"[cyan]DEBUG: Received action type: {action_type}[/cyan]"
            )

        if action_type == "message":
            # Content is handled in _send_message for streaming
            pass
        elif action_type == "file":
            await self._handle_file_action(action)
        else:
            await self._handle_non_file_action(action)

    async def _handle_non_file_action(self, action: Dict[str, Any]) -> None:
        """Handle non-file actions that can be processed during Live streaming."""
        action_type = action.get("type")

        if self.config.debug:
            self.console.print(
                f"[cyan]DEBUG: Handling non-file action: {action_type}[/cyan]"
            )

        if action_type == "tool_use":
            description = action.get("description") or action.get("tool_name", "tool")
            self.console.print(f"[dim]( {description} )…[/dim]")
        elif action_type == "limit_message":
            content = action.get("content", "")
            if content:
                self.console.print(f"[dim]{content}[/dim]")
        else:
            # Unknown action type, just print it
            if self.config.debug:
                self.console.print(f"[yellow]Unknown action type: {action}[/yellow]")

    async def _handle_file_action(self, action: Dict[str, Any]) -> None:
        """Delegate file actions to utility handler."""
        await handle_file_action(self.console, action, debug=self.config.debug)

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
