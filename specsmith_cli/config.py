"""Configuration management for the SpecSmith CLI."""

import base64
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple


@dataclass
class Config:
    """Configuration for the SpecSmith CLI."""

    api_url: str
    access_key_id: str
    access_key_token: str
    debug: bool = False

    @property
    def auth_header(self) -> str:
        """Generate the Basic Auth header."""
        credentials = f"{self.access_key_id}:{self.access_key_token}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"


def get_config_dir() -> Path:
    """Get the configuration directory."""
    return Path.home() / ".specsmith"


def get_credentials_file() -> Path:
    """Get the credentials file path."""
    return get_config_dir() / "credentials"


def load_credentials_from_file() -> Optional[Tuple[str, str]]:
    """Load credentials from the config file."""
    cred_file = get_credentials_file()

    if not cred_file.exists():
        return None

    try:
        with open(cred_file, "r") as f:
            lines = f.readlines()

        access_key_id = None
        access_key_token = None

        for line in lines:
            line = line.strip()
            if line.startswith("access_key_id="):
                access_key_id = line.split("=", 1)[1]
            elif line.startswith("access_key_token="):
                access_key_token = line.split("=", 1)[1]

        if access_key_id and access_key_token:
            return access_key_id, access_key_token

    except Exception:
        pass

    return None


def save_credentials_to_file(access_key_id: str, access_key_token: str) -> None:
    """Save credentials to the config file."""
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)

    cred_file = get_credentials_file()
    with open(cred_file, "w") as f:
        f.write(f"access_key_id={access_key_id}\n")
        f.write(f"access_key_token={access_key_token}\n")

    # Set restrictive permissions
    cred_file.chmod(0o600)


def load_config(
    api_url: Optional[str] = None,
    access_key_id: Optional[str] = None,
    access_key_token: Optional[str] = None,
    debug: bool = False,
) -> Config:
    """Load configuration from various sources."""

    # API URL: command line > environment > default
    final_api_url = api_url or os.getenv("SPECSMITH_API_URL") or "http://localhost:8000"

    # Access key ID: command line > environment > config file
    final_access_key_id = access_key_id or os.getenv("SPECSMITH_ACCESS_KEY_ID")
    final_access_key_token = access_key_token or os.getenv("SPECSMITH_ACCESS_KEY_TOKEN")

    # If not provided via command line or environment, try config file
    if not final_access_key_id or not final_access_key_token:
        file_creds = load_credentials_from_file()
        if file_creds:
            file_key_id, file_key_token = file_creds
            final_access_key_id = final_access_key_id or file_key_id
            final_access_key_token = final_access_key_token or file_key_token

    # Debug: command line > environment
    final_debug = debug or os.getenv("SPECSMITH_DEBUG", "").lower() in (
        "1",
        "true",
        "yes",
    )

    if not final_access_key_id or not final_access_key_token:
        raise ValueError(
            "API credentials not found. Please set them via:\n"
            "1. Environment variables: SPECSMITH_ACCESS_KEY_ID and SPECSMITH_ACCESS_KEY_TOKEN\n"
            "2. Config file: ~/.specsmith/credentials\n"
            "3. Command line arguments: --access-key-id and --access-key-token"
        )

    return Config(
        api_url=final_api_url,
        access_key_id=final_access_key_id,
        access_key_token=final_access_key_token,
        debug=final_debug,
    )


def setup_credentials_interactive() -> None:
    """Set up credentials interactively."""
    print("Setting up SpecSmith CLI credentials...")
    print("You can get your API keys from the SpecSmith web interface.")
    print()

    access_key_id = input("Enter your Access Key ID: ").strip()
    access_key_token = input("Enter your Access Key Token: ").strip()

    if not access_key_id or not access_key_token:
        print("❌ Both Access Key ID and Access Key Token are required.")
        return

    try:
        save_credentials_to_file(access_key_id, access_key_token)
        print("✅ Credentials saved to ~/.specsmith/credentials")
    except Exception as e:
        print(f"❌ Failed to save credentials: {e}")


def validate_credentials(config: Config) -> bool:
    """Validate that the credentials are properly formatted."""
    try:
        # Check for empty credentials
        if not config.access_key_id or not config.access_key_token:
            return False

        # Test that we can create the auth header
        auth_header = config.auth_header
        if not auth_header.startswith("Basic "):
            return False

        # Test base64 decoding
        encoded_part = auth_header[6:]  # Remove "Basic "
        decoded = base64.b64decode(encoded_part).decode()
        if ":" not in decoded:
            return False

        return True
    except Exception:
        return False
