"""Tests for the configuration module."""

import os
import tempfile
from pathlib import Path

import pytest

from specsmith_cli.config import (
    Config,
    get_config_dir,
    get_credentials_file,
    load_config,
    load_credentials_from_file,
    save_credentials_to_file,
    validate_credentials,
)


def test_config_auth_header():
    """Test that the auth header is generated correctly."""
    config = Config(
        api_url="http://localhost:8000",
        access_key_id="test-id",
        access_key_token="test-token",
    )

    auth_header = config.auth_header
    assert auth_header.startswith("Basic ")

    # Decode and verify
    import base64

    encoded_part = auth_header[6:]  # Remove "Basic "
    decoded = base64.b64decode(encoded_part).decode()
    assert decoded == "test-id:test-token"


def test_get_config_dir():
    """Test getting the config directory."""
    config_dir = get_config_dir()
    assert config_dir == Path.home() / ".specsmith"


def test_get_credentials_file():
    """Test getting the credentials file path."""
    cred_file = get_credentials_file()
    assert cred_file == Path.home() / ".specsmith" / "credentials"


def test_save_and_load_credentials():
    """Test saving and loading credentials from file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the home directory
        original_home = Path.home
        Path.home = lambda: Path(temp_dir)

        try:
            # Test saving credentials
            save_credentials_to_file("test-id", "test-token")

            # Test loading credentials
            creds = load_credentials_from_file()
            assert creds is not None
            access_key_id, access_key_token = creds
            assert access_key_id == "test-id"
            assert access_key_token == "test-token"

        finally:
            # Restore original home function
            Path.home = original_home


def test_load_credentials_from_nonexistent_file():
    """Test loading credentials when file doesn't exist."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Mock the home directory
        original_home = Path.home
        Path.home = lambda: Path(temp_dir)

        try:
            creds = load_credentials_from_file()
            assert creds is None
        finally:
            Path.home = original_home


def test_load_config_with_environment():
    """Test loading config from environment variables."""
    # Set environment variables
    os.environ["SPECSMITH_API_URL"] = "http://test-api:9000"
    os.environ["SPECSMITH_ACCESS_KEY_ID"] = "env-id"
    os.environ["SPECSMITH_ACCESS_KEY_TOKEN"] = "env-token"
    os.environ["SPECSMITH_DEBUG"] = "true"

    try:
        config = load_config()
        assert config.api_url == "http://test-api:9000"
        assert config.access_key_id == "env-id"
        assert config.access_key_token == "env-token"
        assert config.debug is True
    finally:
        # Clean up environment variables
        for key in [
            "SPECSMITH_API_URL",
            "SPECSMITH_ACCESS_KEY_ID",
            "SPECSMITH_ACCESS_KEY_TOKEN",
            "SPECSMITH_DEBUG",
        ]:
            os.environ.pop(key, None)


def test_load_config_with_arguments():
    """Test loading config with command line arguments."""
    config = load_config(
        api_url="http://arg-api:8000",
        access_key_id="arg-id",
        access_key_token="arg-token",
        debug=True,
    )

    assert config.api_url == "http://arg-api:8000"
    assert config.access_key_id == "arg-id"
    assert config.access_key_token == "arg-token"
    assert config.debug is True


def test_load_config_missing_credentials():
    """Test loading config when credentials are missing."""
    # Temporarily remove environment variables
    original_env = {}
    for key in ["SPECSMITH_ACCESS_KEY_ID", "SPECSMITH_ACCESS_KEY_TOKEN"]:
        if key in os.environ:
            original_env[key] = os.environ[key]
            del os.environ[key]

    # Mock the credentials file to return None
    original_load_creds = load_credentials_from_file
    try:
        # Mock the function to return None
        import specsmith_cli.config

        specsmith_cli.config.load_credentials_from_file = lambda: None

        with pytest.raises(ValueError, match="API credentials not found"):
            load_config()
    finally:
        # Restore environment variables and function
        for key, value in original_env.items():
            os.environ[key] = value
        specsmith_cli.config.load_credentials_from_file = original_load_creds


def test_validate_credentials():
    """Test credential validation."""
    config = Config(
        api_url="http://localhost:8000",
        access_key_id="test-id",
        access_key_token="test-token",
    )

    assert validate_credentials(config) is True


def test_validate_credentials_invalid():
    """Test credential validation with invalid credentials."""
    config = Config(
        api_url="http://localhost:8000",
        access_key_id="",  # Empty
        access_key_token="test-token",
    )

    # The current implementation doesn't validate empty strings
    # Let's test with a more obviously invalid case
    config2 = Config(
        api_url="http://localhost:8000",
        access_key_id="test-id",
        access_key_token="",  # Empty token
    )

    # Both should be invalid
    assert validate_credentials(config) is False
    assert validate_credentials(config2) is False
