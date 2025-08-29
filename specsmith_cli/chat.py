"""Chat interface for the Specsmith CLI."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Confirm
from rich.text import Text

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
        self.history: list[
            dict[str, str]
        ] = []  # {role: "user|assistant|system", content: str}

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

    # Removed fullscreen application helpers

    def _show_welcome_screen(self) -> None:
        """Display the Claude Code-style welcome screen with panels."""
        # Clear screen
        os.system("clear" if os.name == "posix" else "cls")

        # Welcome panel with Specsmith brand colors
        welcome_panel = Panel(
            "[#D4A63D]✻ Welcome to Specsmith Agent![/]\n\n  How can I help you today?\n  I can help you create, refine, and manage software specifications.\n",
            title=None,
            border_style="#6AA9FF",  # Blueprint Wash blue
            padding=(1, 2),
        )
        self.console.print(welcome_panel)

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
        # Do not print an extra blank line here; spacing is handled by callers

        lines = []
        first_line = True

        while True:
            if first_line:
                prompt = HTML("<ansibrightblack>> </ansibrightblack>")
                first_line = False
            else:
                prompt = HTML("<ansibrightblack>  \\ </ansibrightblack>")

            try:
                # Prompt for a line; we'll explicitly clear it from the terminal afterwards
                line = await self.prompt_session.prompt_async(
                    prompt,
                    style=self.style,
                )
            except EOFError:
                # Ctrl+D pressed - propagate the EOFError to be handled by the main loop
                raise

            # Strip any trailing whitespace first
            line = line.rstrip()

            # Clear the previously echoed input line so only the panel shows the user message
            # Emit ANSI escape sequences directly to the underlying stream
            try:
                stream = self.console.file
                stream.write("\x1b[1A\r\x1b[K")
                stream.flush()
            except Exception:
                # If the terminal does not support ANSI, ignore
                pass

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
        # Ensure exactly one blank line before showing the user panel
        self.console.print()
        self.console.print(user_panel)
        # And exactly one blank line after the user panel before assistant output
        self.console.print()

    async def _send_message(self, message: str) -> None:
        """Send a message and stream the response using Rich Live panel."""
        if not self.api_client or not self.session_id:
            raise ValueError("API client or session not initialized")

        try:
            response_text = ""
            # Ensure a blank line precedes assistant output for consistent spacing
            self.console.print()

            # Start with empty Markdown object for consistency
            with Live(
                Markdown(""), refresh_per_second=10, console=self.console
            ) as live:
                async for action in self.api_client.send_message(
                    self.session_id, message
                ):
                    if action.get("type") == "message":
                        content = action.get("content", "")
                        if content:
                            response_text += content
                            # Apply markdown normalization before rendering
                            normalized_text = self._normalize_markdown_alignment(
                                response_text
                            )
                            live.update(Markdown(normalized_text))
                    else:
                        await self._handle_action(action)

            # One trailing blank line after assistant output to separate from next turn
            self.console.print()

        except Exception as e:
            self.console.print(f"[red]❌ Error: {e}[/red]")

    async def _handle_action(self, action: Dict[str, Any]) -> None:
        """Handle different types of actions from the API."""
        action_type = action.get("type")

        if action_type == "message":
            # Content is handled in _send_message for streaming
            pass

        elif action_type == "file":
            await self._handle_file_action(action)
        elif action_type == "tool_use":
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
