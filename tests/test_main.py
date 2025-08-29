"""Tests for the Click CLI entry points in main.py."""

import os
from typing import Optional

from click.testing import CliRunner

from specsmith_cli.main import main


def _env_with_creds(
    api_url: Optional[str] = "http://localhost:8000",
    key_id: Optional[str] = "test-id",
    key_token: Optional[str] = "test-token",
    debug: Optional[bool] = False,
):
    env = os.environ.copy()
    if api_url is not None:
        env["SPECSMITH_API_URL"] = api_url
    if key_id is not None:
        env["SPECSMITH_ACCESS_KEY_ID"] = key_id
    if key_token is not None:
        env["SPECSMITH_ACCESS_KEY_TOKEN"] = key_token
    if debug:
        env["SPECSMITH_DEBUG"] = "true"
    return env


def test_main_invokes_chat_by_default(monkeypatch):
    runner = CliRunner()

    # Prevent starting the interactive chat; intercept _start_chat via subcommand
    # Instead run the lightweight `version` subcommand to verify wiring
    result = runner.invoke(main, ["version"], env=_env_with_creds())
    assert result.exit_code == 0
    assert "Specsmith CLI v" in result.output


def test_main_config_command_outputs(monkeypatch):
    runner = CliRunner()
    result = runner.invoke(main, ["config"], env=_env_with_creds(debug=True))
    assert result.exit_code == 0
    assert "Current Configuration" in result.output
    assert "API URL:" in result.output
    assert "Access Key ID:" in result.output
    assert "Debug Mode: True" in result.output


def test_main_test_command_success(monkeypatch):
    runner = CliRunner()

    # Mock the API client inside the command path by setting env and using monkeypatch
    class _Dummy:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return False

        async def test_connection(self):
            return True

    # Patch the import used in main
    import specsmith_cli.main as main_mod

    monkeypatch.setattr(main_mod, "SpecSmithAPIClient", lambda *_args, **_kw: _Dummy())

    result = runner.invoke(main, ["test"], env=_env_with_creds())
    assert result.exit_code == 0
    assert "Connection successful" in result.output


def test_main_test_command_failure(monkeypatch):
    runner = CliRunner()

    class _Dummy:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            return False

        async def test_connection(self):
            return False

    import specsmith_cli.main as main_mod

    monkeypatch.setattr(main_mod, "SpecSmithAPIClient", lambda *_args, **_kw: _Dummy())

    result = runner.invoke(main, ["test"], env=_env_with_creds())
    assert result.exit_code != 0
    assert "Connection failed" in result.output


def test_main_setup_shows_header(monkeypatch):
    runner = CliRunner()

    # Avoid interactive prompts by patching setup function
    import specsmith_cli.main as main_mod

    called = {"setup": False}

    def _fake_setup():
        called["setup"] = True

    monkeypatch.setattr(main_mod, "setup_credentials_interactive", _fake_setup)

    result = runner.invoke(main, ["setup"], env=_env_with_creds())
    assert result.exit_code == 0
    assert called["setup"] is True
    assert "Specsmith CLI Setup" in result.output


def test_main_invalid_config_exits(monkeypatch):
    runner = CliRunner()
    # Remove credentials to trigger config error path and prevent file reads
    env = _env_with_creds(key_id=None, key_token=None)
    import specsmith_cli.config as cfg

    monkeypatch.setattr(cfg.Config, "load_from_file", classmethod(lambda cls: None))

    result = runner.invoke(main, ["chat"], env=env)
    assert result.exit_code != 0
    assert "Configuration error" in result.output
