"""CLI utilities for Specsmith."""

from pathlib import Path
from typing import Any, Dict

from rich.console import Console
from rich.prompt import Confirm


async def handle_file_action(
    console: Console, action: Dict[str, Any], debug: bool = False
) -> None:
    """Handle file actions with user prompts and saving logic.

    Parameters:
    - console: Rich Console to print to
    - action: dict containing 'filename' and 'content'
    - debug: whether to emit debug lines
    """
    filename = action.get("filename", "")
    content = action.get("content", "")

    if debug:
        console.print(
            f"[cyan]DEBUG: File action received - filename: {filename}, content length: {len(content) if content else 0}[/cyan]"
        )

    if not filename or not content:
        if debug:
            console.print("[cyan]DEBUG: Missing filename or content, skipping[/cyan]")
        return

    file_path = Path(filename)

    # Check if file exists
    if file_path.exists():
        if debug:
            console.print("[cyan]DEBUG: File exists, asking for overwrite[/cyan]")
        overwrite = Confirm.ask(
            f"\n[cyan][italic]Before we continue, would you like to overwrite[/italic] '{filename}'[italic]?[/italic][/]",
            default=False,
        )
        if not overwrite:
            console.print(f"[yellow]Skipped saving {filename}[/yellow]")
            return
    else:
        if debug:
            console.print("[cyan]DEBUG: File doesn't exist, asking to save[/cyan]")
        # File doesn't exist, ask for save with content summary
        content_lines = len(content.splitlines()) if content else 0
        content_size = (
            f"{len(content)} chars, {content_lines} lines" if content else "empty"
        )
        save = Confirm.ask(
            f"\n[cyan][italic]Before we continue, would you like to save file[/italic] '{filename}' [italic]({content_size})?[/italic][/]",
            default=True,
        )
        if not save:
            console.print(f"[yellow]Skipped saving {filename}[/yellow]")
            return

    # Save the file
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            f.write(content)
        console.print(f"[green]✅ Saved {filename}[/green]")
    except Exception as e:
        console.print(f"[red]❌ Failed to save {filename}: {e}[/red]")
