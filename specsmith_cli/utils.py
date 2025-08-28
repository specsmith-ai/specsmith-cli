"""Utility functions for the Specsmith CLI."""

import os
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.prompt import Confirm

console = Console()


def get_current_directory() -> Path:
    """Get the current working directory."""
    return Path.cwd()


def check_file_exists(filename: str) -> bool:
    """Check if a file exists in the current directory."""
    return Path(filename).exists()


def ensure_directory_exists(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)


def get_home_directory() -> Path:
    """Get the user's home directory."""
    return Path.home()


def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    return os.getenv("SPECSMITH_DEBUG", "").lower() in ("1", "true", "yes")


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[red]❌ {message}[/red]")


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]✅ {message}[/green]")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[yellow]⚠️  {message}[/yellow]")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[blue]ℹ️  {message}[/blue]")


def safe_filename(filename: str) -> str:
    """Convert a filename to a safe version."""
    # Remove or replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, "_")

    # Remove leading/trailing spaces and dots
    filename = filename.strip(". ")

    # Ensure it's not empty
    if not filename:
        filename = "untitled"

    return filename


def get_file_extension(filename: str) -> str:
    """Get the file extension from a filename."""
    return Path(filename).suffix


def suggest_filename(base_name: str, extension: str = "") -> str:
    """Suggest a filename based on content."""
    if not extension:
        extension = ".txt"

    # Clean the base name
    safe_base = safe_filename(base_name)

    # Limit length
    if len(safe_base) > 50:
        safe_base = safe_base[:50]

    return f"{safe_base}{extension}"


def confirm_overwrite(filename: str) -> bool:
    """Ask user to confirm file overwrite."""
    return Confirm.ask(
        f"File '{filename}' already exists. Do you want to overwrite it?", default=False
    )


def confirm_save(filename: str) -> bool:
    """Ask user to confirm file save."""
    return Confirm.ask(f"Save file '{filename}'?", default=True)


def write_file_safely(filepath: Path, content: str) -> bool:
    """Write content to a file with error handling."""
    try:
        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Write content
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return True
    except Exception as e:
        print_error(f"Failed to save {filepath}: {e}")
        return False


def read_file_safely(filepath: Path) -> Optional[str]:
    """Read content from a file with error handling."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print_error(f"Failed to read {filepath}: {e}")
        return None
