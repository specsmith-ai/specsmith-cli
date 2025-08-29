"""Configuration management for the Specsmith CLI."""

import base64
import os
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.prompt import Prompt

from .constants import DEFAULT_API_URL

console = Console()


class Config:
    """Configuration for the Specsmith CLI."""

    def __init__(
        self,
        api_url: str,
        access_key_id: str,
        access_key_token: str,
        debug: bool = False,
    ):
        self.api_url = api_url.rstrip("/")
        self.access_key_id = access_key_id
        self.access_key_token = access_key_token
        self.debug = debug

    @property
    def auth_header(self) -> str:
        """Get the authorization header for API requests."""
        credentials = f"{self.access_key_id}:{self.access_key_token}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded_credentials}"

    @classmethod
    def get_config_dir(cls) -> Path:
        """Get the configuration directory."""
        return Path.home() / ".specsmith"

    @classmethod
    def get_credentials_file(cls) -> Path:
        """Get the credentials file path."""
        return cls.get_config_dir() / "credentials"

    @classmethod
    def load_from_file(cls) -> Optional["Config"]:
        """Load configuration from file."""
        credentials_file = cls.get_credentials_file()

        if not credentials_file.exists():
            return None

        try:
            with open(credentials_file, "r") as f:
                content = f.read()

            # Parse key=value format
            config_dict = {}
            for line in content.splitlines():
                line = line.strip()
                if line and "=" in line:
                    key, value = line.split("=", 1)
                    config_dict[key.strip()] = value.strip()

            # Extract values with defaults
            api_url = config_dict.get("api_url", DEFAULT_API_URL)
            access_key_id = config_dict.get("access_key_id")
            access_key_token = config_dict.get("access_key_token")
            debug = config_dict.get("debug", "false").lower() == "true"

            if not access_key_id or not access_key_token:
                return None

            return cls(api_url, access_key_id, access_key_token, debug)

        except Exception:
            return None

    def save_to_file(self) -> None:
        """Save configuration to file."""
        config_dir = self.get_config_dir()
        config_dir.mkdir(parents=True, exist_ok=True)

        credentials_file = self.get_credentials_file()
        with open(credentials_file, "w") as f:
            f.write(f"api_url={self.api_url}\n")
            f.write(f"access_key_id={self.access_key_id}\n")
            f.write(f"access_key_token={self.access_key_token}\n")
            f.write(f"debug={str(self.debug).lower()}\n")


def load_config(
    api_url: Optional[str] = None,
    access_key_id: Optional[str] = None,
    access_key_token: Optional[str] = None,
    debug: Optional[bool] = None,
) -> Config:
    """Load configuration from various sources."""
    # First, read any config from file for fallback purposes
    file_config = Config.load_from_file()

    # Environment variables and CLI options take precedence
    final_api_url = api_url or os.getenv("SPECSMITH_API_URL")
    final_access_key_id = access_key_id or os.getenv("SPECSMITH_ACCESS_KEY_ID")
    final_access_key_token = access_key_token or os.getenv("SPECSMITH_ACCESS_KEY_TOKEN")
    final_debug = debug or os.getenv("SPECSMITH_DEBUG", "").lower() in (
        "1",
        "true",
        "yes",
    )

    # Fall back to file values where not provided
    if not final_api_url and file_config:
        final_api_url = file_config.api_url
    if (not final_access_key_id or not final_access_key_token) and file_config:
        final_access_key_id = final_access_key_id or file_config.access_key_id
        final_access_key_token = final_access_key_token or file_config.access_key_token
        final_debug = final_debug or file_config.debug

    # Final fallback to defaults
    final_api_url = final_api_url or DEFAULT_API_URL

    if not final_access_key_id or not final_access_key_token:
        raise ValueError(
            "API credentials not found. Please set up credentials using:\n"
            "1. Environment variables: SPECSMITH_ACCESS_KEY_ID and SPECSMITH_ACCESS_KEY_TOKEN\n"
            "2. Config file: ~/.specsmith/credentials\n"
            "3. Run 'specsmith setup' to configure interactively"
        )

    return Config(
        final_api_url, final_access_key_id, final_access_key_token, final_debug
    )


def setup_credentials_interactive() -> None:
    """Set up credentials interactively."""
    console.print("Setting up Specsmith CLI credentials...")
    console.print("You can get your API keys from the Specsmith web interface.")
    console.print()

    access_key_id = Prompt.ask("Access Key ID")
    access_key_token = Prompt.ask("Access Key Token", password=True)

    config = Config(DEFAULT_API_URL, access_key_id, access_key_token)
    config.save_to_file()

    console.print("✅ Credentials saved to ~/.specsmith/credentials")


def validate_credentials(config: Config) -> bool:
    """Validate that credentials are properly formatted."""
    if not config.access_key_id or not config.access_key_token:
        return False
    return True
