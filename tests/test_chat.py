"""Tests for the chat module."""

from unittest.mock import AsyncMock, patch

import pytest
from rich.console import Console

from specsmith_cli.chat import ChatInterface, run_chat
from specsmith_cli.config import Config


@pytest.fixture
def config():
    """Create a test configuration."""
    return Config(
        api_url="http://localhost:8000",
        access_key_id="test-key",
        access_key_token="test-secret",
        debug=False,
    )


@pytest.fixture
def debug_config():
    """Create a test configuration with debug enabled."""
    return Config(
        api_url="http://localhost:8000",
        access_key_id="test-key",
        access_key_token="test-secret",
        debug=True,
    )


class TestChatInterface:
    """Test cases for ChatInterface class."""

    def test_init(self, config):
        """Test ChatInterface initialization."""
        chat = ChatInterface(config)

        assert chat.config == config
        assert isinstance(chat.console, Console)
        assert chat.session_id is None
        assert chat.api_client is None

    @pytest.mark.asyncio
    async def test_start_success(self, config):
        """Test successful chat start."""
        with patch("specsmith_cli.chat.SpecSmithAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock successful connection test and session creation
            mock_client.test_connection.return_value = True
            mock_client.create_session.return_value = "test-session-123"

            chat = ChatInterface(config)

            # Mock the interactive loop to avoid infinite loop
            with patch.object(chat, "_interactive_loop") as mock_loop:
                await chat.start()

                # Verify API client was initialized
                mock_client_class.assert_called_once_with(config)

                # Verify connection was tested
                mock_client.test_connection.assert_called_once()

                # Verify session was created
                mock_client.create_session.assert_called_once()

                # Verify session ID was set
                assert chat.session_id == "test-session-123"

                # Verify interactive loop was called
                mock_loop.assert_called_once()

                # Verify client was closed
                mock_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_connection_failure(self, config):
        """Test chat start with connection failure."""
        with patch("specsmith_cli.chat.SpecSmithAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock failed connection test
            mock_client.test_connection.return_value = False

            chat = ChatInterface(config)

            with patch.object(chat.console, "print") as mock_print:
                await chat.start()

                # Verify connection was tested
                mock_client.test_connection.assert_called_once()

                # Verify session was NOT created
                mock_client.create_session.assert_not_called()

                # Verify error messages were printed
                assert mock_print.call_count >= 4  # Multiple error messages

                # Verify client was closed
                mock_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_exception_handling(self, config):
        """Test chat start with exception."""
        with patch("specsmith_cli.chat.SpecSmithAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock exception during connection test
            mock_client.test_connection.side_effect = Exception("Connection error")

            chat = ChatInterface(config)

            with patch.object(chat.console, "print") as mock_print:
                await chat.start()

                # Verify error was printed
                mock_print.assert_called_with("[red]❌ Error: Connection error[/red]")

                # Verify client was closed
                mock_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_interactive_loop_quit_commands(self, config):
        """Test interactive loop with quit commands."""
        chat = ChatInterface(config)

        # Test different quit commands
        quit_commands = ["quit", "exit", "q", "QUIT", "EXIT"]

        for quit_cmd in quit_commands:
            with patch.object(chat, "_get_multiline_input", return_value=quit_cmd):
                with patch.object(chat.console, "print") as mock_print:
                    await chat._interactive_loop()

                    # Should print goodbye message
                    mock_print.assert_called_with("[dim]Goodbye![/dim]")

    @pytest.mark.asyncio
    async def test_interactive_loop_empty_message(self, config):
        """Test interactive loop with empty messages."""
        chat = ChatInterface(config)

        # Mock prompt to return empty string, then quit
        with patch.object(
            chat, "_get_multiline_input", side_effect=["", "   ", "quit"]
        ):
            with patch.object(chat, "_send_message") as mock_send:
                with patch.object(chat.console, "print"):
                    await chat._interactive_loop()

                    # Should not call send_message for empty inputs
                    mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_interactive_loop_keyboard_interrupt(self, config):
        """Test interactive loop with keyboard interrupt."""
        chat = ChatInterface(config)

        with patch.object(
            chat, "_get_multiline_input", side_effect=KeyboardInterrupt()
        ):
            with patch.object(chat.console, "print") as mock_print:
                await chat._interactive_loop()

                # Should print goodbye message
                mock_print.assert_called_with("\n[dim]Goodbye![/dim]")

    @pytest.mark.asyncio
    async def test_interactive_loop_exception_handling(self, config):
        """Test interactive loop with exception handling."""
        chat = ChatInterface(config)

        # Mock prompt to raise exception, then quit
        with patch.object(
            chat, "_get_multiline_input", side_effect=[Exception("Input error"), "quit"]
        ):
            with patch.object(chat.console, "print") as mock_print:
                await chat._interactive_loop()

                # Should print error message
                error_calls = [
                    call
                    for call in mock_print.call_args_list
                    if "[red]❌ Error: Input error[/red]" in str(call)
                ]
                assert len(error_calls) > 0

    @pytest.mark.asyncio
    async def test_send_message_success(self, config):
        """Test successful message sending."""
        chat = ChatInterface(config)
        chat.api_client = AsyncMock()
        chat.session_id = "test-session"

        # Mock streaming response
        async def mock_send_message(session_id, message):
            yield {"type": "message", "content": "Hello "}
            yield {"type": "message", "content": "World!"}
            yield {"type": "tool_use", "description": "searching"}

        chat.api_client.send_message = mock_send_message

        with patch.object(chat, "_handle_action") as mock_handle:
            await chat._send_message("test message")

            # Should handle non-message action
            mock_handle.assert_called_once_with(
                {"type": "tool_use", "description": "searching"}
            )

    @pytest.mark.asyncio
    async def test_send_message_no_client(self, config):
        """Test send message without initialized client."""
        chat = ChatInterface(config)

        with pytest.raises(ValueError, match="API client or session not initialized"):
            await chat._send_message("test message")

    @pytest.mark.asyncio
    async def test_send_message_no_session(self, config):
        """Test send message without session."""
        chat = ChatInterface(config)
        chat.api_client = AsyncMock()
        # session_id remains None

        with pytest.raises(ValueError, match="API client or session not initialized"):
            await chat._send_message("test message")

    @pytest.mark.asyncio
    async def test_send_message_exception(self, config):
        """Test send message with exception."""
        chat = ChatInterface(config)
        chat.api_client = AsyncMock()
        chat.session_id = "test-session"

        # Mock exception during message sending
        async def mock_send_message_error(session_id, message):
            raise Exception("Send error")
            yield  # This won't be reached

        chat.api_client.send_message = mock_send_message_error

        with patch.object(chat.console, "print") as mock_print:
            await chat._send_message("test message")

            # Should print error message
            mock_print.assert_called_with("[red]❌ Error: Send error[/red]")

    @pytest.mark.asyncio
    async def test_handle_action_message(self, config):
        """Test handling message action."""
        chat = ChatInterface(config)

        # Message actions are handled in _send_message, so this should do nothing
        await chat._handle_action({"type": "message", "content": "test"})

    @pytest.mark.asyncio
    async def test_handle_action_file(self, config):
        """Test handling file action."""
        chat = ChatInterface(config)

        with patch.object(chat, "_handle_file_action") as mock_handle_file:
            await chat._handle_action({"type": "file", "filename": "test.py"})

            mock_handle_file.assert_called_once_with(
                {"type": "file", "filename": "test.py"}
            )

    @pytest.mark.asyncio
    async def test_handle_action_tool_use(self, config):
        """Test handling tool use action."""
        chat = ChatInterface(config)

        with patch.object(chat.console, "print") as mock_print:
            # Test with description
            await chat._handle_action(
                {"type": "tool_use", "description": "searching files"}
            )
            mock_print.assert_called_with("[dim]( searching files )…[/dim]")

            # Test with tool_name fallback
            mock_print.reset_mock()
            await chat._handle_action({"type": "tool_use", "tool_name": "search"})
            mock_print.assert_called_with("[dim]( search )…[/dim]")

            # Test with neither (fallback to "tool")
            mock_print.reset_mock()
            await chat._handle_action({"type": "tool_use"})
            mock_print.assert_called_with("[dim]( tool )…[/dim]")

    @pytest.mark.asyncio
    async def test_handle_action_limit_message(self, config):
        """Test handling limit message action."""
        chat = ChatInterface(config)

        with patch.object(chat.console, "print") as mock_print:
            await chat._handle_action(
                {"type": "limit_message", "content": "Rate limit reached"}
            )

            mock_print.assert_called_with("[dim]Rate limit reached[/dim]")

    @pytest.mark.asyncio
    async def test_handle_action_unknown_debug(self, debug_config):
        """Test handling unknown action with debug enabled."""
        chat = ChatInterface(debug_config)

        with patch.object(chat.console, "print") as mock_print:
            unknown_action = {"type": "unknown", "data": "test"}
            await chat._handle_action(unknown_action)

            mock_print.assert_called_with(
                f"[yellow]Unknown action type: {unknown_action}[/yellow]"
            )

    @pytest.mark.asyncio
    async def test_handle_action_unknown_no_debug(self, config):
        """Test handling unknown action with debug disabled."""
        chat = ChatInterface(config)

        with patch.object(chat.console, "print") as mock_print:
            await chat._handle_action({"type": "unknown", "data": "test"})

            # Should not print anything when debug is False
            mock_print.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_file_action_new_file_save(self, config, tmp_path):
        """Test handling file action for new file with save confirmation."""
        chat = ChatInterface(config)

        test_file = tmp_path / "test.py"
        file_content = "print('Hello, World!')"

        action = {"filename": str(test_file), "content": file_content}

        with patch("rich.prompt.Confirm.ask", return_value=True):
            with patch.object(chat.console, "print") as mock_print:
                await chat._handle_file_action(action)

                # File should be created
                assert test_file.exists()
                assert test_file.read_text() == file_content

                # Should print success message
                mock_print.assert_called_with(f"[green]✅ Saved {test_file}[/green]")

    @pytest.mark.asyncio
    async def test_handle_file_action_new_file_skip(self, config, tmp_path):
        """Test handling file action for new file with skip."""
        chat = ChatInterface(config)

        test_file = tmp_path / "test.py"

        action = {"filename": str(test_file), "content": "print('Hello, World!')"}

        with patch("rich.prompt.Confirm.ask", return_value=False):
            with patch.object(chat.console, "print") as mock_print:
                await chat._handle_file_action(action)

                # File should not be created
                assert not test_file.exists()

                # Should print skip message
                mock_print.assert_called_with(
                    f"[yellow]Skipped saving {test_file}[/yellow]"
                )

    @pytest.mark.asyncio
    async def test_handle_file_action_existing_file_overwrite(self, config, tmp_path):
        """Test handling file action for existing file with overwrite."""
        chat = ChatInterface(config)

        test_file = tmp_path / "existing.py"
        test_file.write_text("old content")

        new_content = "new content"
        action = {"filename": str(test_file), "content": new_content}

        with patch("rich.prompt.Confirm.ask", return_value=True):
            with patch.object(chat.console, "print") as mock_print:
                await chat._handle_file_action(action)

                # File should be overwritten
                assert test_file.read_text() == new_content

                # Should print success message
                mock_print.assert_called_with(f"[green]✅ Saved {test_file}[/green]")

    @pytest.mark.asyncio
    async def test_handle_file_action_existing_file_no_overwrite(
        self, config, tmp_path
    ):
        """Test handling file action for existing file without overwrite."""
        chat = ChatInterface(config)

        test_file = tmp_path / "existing.py"
        original_content = "original content"
        test_file.write_text(original_content)

        action = {"filename": str(test_file), "content": "new content"}

        with patch("rich.prompt.Confirm.ask", return_value=False):
            with patch.object(chat.console, "print") as mock_print:
                await chat._handle_file_action(action)

                # File should remain unchanged
                assert test_file.read_text() == original_content

                # Should print skip message
                mock_print.assert_called_with(
                    f"[yellow]Skipped saving {test_file}[/yellow]"
                )

    @pytest.mark.asyncio
    async def test_handle_file_action_missing_data(self, config):
        """Test handling file action with missing filename or content."""
        chat = ChatInterface(config)

        # Test missing filename
        await chat._handle_file_action({"content": "test"})

        # Test missing content
        await chat._handle_file_action({"filename": "test.py"})

        # Test both missing
        await chat._handle_file_action({})

        # Should not raise any exceptions

    @pytest.mark.asyncio
    async def test_handle_file_action_directory_creation(self, config, tmp_path):
        """Test handling file action with directory creation."""
        chat = ChatInterface(config)

        nested_file = tmp_path / "subdir" / "nested" / "test.py"

        action = {"filename": str(nested_file), "content": "test content"}

        with patch("rich.prompt.Confirm.ask", return_value=True):
            await chat._handle_file_action(action)

            # File and directories should be created
            assert nested_file.exists()
            assert nested_file.read_text() == "test content"

    @pytest.mark.asyncio
    async def test_handle_file_action_write_error(self, config):
        """Test handling file action with write error."""
        chat = ChatInterface(config)

        # Try to write to an invalid path
        action = {"filename": "/invalid/path/test.py", "content": "test content"}

        with patch("rich.prompt.Confirm.ask", return_value=True):
            with patch.object(chat.console, "print") as mock_print:
                await chat._handle_file_action(action)

                # Should print error message
                error_calls = [
                    call
                    for call in mock_print.call_args_list
                    if "❌ Failed to save" in str(call)
                ]
                assert len(error_calls) > 0

    @pytest.mark.asyncio
    async def test_send_single_message_success(self, config):
        """Test send_single_message method."""
        chat = ChatInterface(config)

        with patch("specsmith_cli.chat.SpecSmithAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.create_session.return_value = "test-session"

            with patch.object(chat, "_send_message") as mock_send:
                await chat.send_single_message("Hello")

                # Should create session and send message
                mock_client.create_session.assert_called_once()
                mock_send.assert_called_once_with("Hello")
                mock_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_single_message_exception(self, config):
        """Test send_single_message with exception."""
        chat = ChatInterface(config)

        with patch("specsmith_cli.chat.SpecSmithAPIClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            mock_client.create_session.side_effect = Exception("Session error")

            with patch.object(chat.console, "print") as mock_print:
                await chat.send_single_message("Hello")

                # Should print error and close client
                mock_print.assert_called_with("[red]❌ Error: Session error[/red]")
                mock_client.aclose.assert_called_once()


class TestRunChat:
    """Test cases for run_chat function."""

    @pytest.mark.asyncio
    async def test_run_chat(self, config):
        """Test run_chat function."""
        with patch("specsmith_cli.chat.ChatInterface") as mock_chat_class:
            mock_chat = AsyncMock()
            mock_chat_class.return_value = mock_chat

            await run_chat(config)

            # Should create ChatInterface and call start
            mock_chat_class.assert_called_once_with(config)
            mock_chat.start.assert_called_once()
