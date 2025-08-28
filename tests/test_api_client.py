"""Tests for the API client module."""

from unittest.mock import AsyncMock, Mock, patch
from contextlib import asynccontextmanager

import httpx
import pytest

from specsmith_cli.api_client import SpecSmithAPIClient, check_api_health
from specsmith_cli.config import Config


@pytest.fixture
def config():
    """Create a test configuration."""
    return Config(
        api_url="http://localhost:8000",
        access_key_id="test-id",
        access_key_token="test-token",
        debug=False,
    )


@pytest.fixture
def debug_config():
    """Create a test configuration with debug enabled."""
    return Config(
        api_url="http://localhost:8000",
        access_key_id="test-id",
        access_key_token="test-token",
        debug=True,
    )


class TestSpecSmithAPIClient:
    """Test cases for SpecSmithAPIClient."""

    @pytest.mark.asyncio
    async def test_health_check_success(self, config):
        """Test successful health check."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response

            client = SpecSmithAPIClient(config)
            client.client = mock_client

            result = await client.health_check()

            assert result is True
            mock_client.get.assert_called_once_with(
                "http://localhost:8000/agent/health"
            )

    @pytest.mark.asyncio
    async def test_health_check_failure(self, config):
        """Test failed health check."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock failed response
            mock_response = Mock()
            mock_response.status_code = 500
            mock_client.get.return_value = mock_response

            client = SpecSmithAPIClient(config)
            client.client = mock_client

            result = await client.health_check()

            assert result is False

    @pytest.mark.asyncio
    async def test_health_check_exception(self, config):
        """Test health check with exception."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock exception
            mock_client.get.side_effect = httpx.ConnectError("Connection failed")

            client = SpecSmithAPIClient(config)
            client.client = mock_client

            result = await client.health_check()

            assert result is False

    @pytest.mark.asyncio
    async def test_create_session_success(self, config):
        """Test successful session creation."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"session_id": "test-session-123"}
            mock_client.post.return_value = mock_response

            client = SpecSmithAPIClient(config)
            client.client = mock_client

            session_id = await client.create_session()

            assert session_id == "test-session-123"
            mock_client.post.assert_called_once_with(
                "http://localhost:8000/agent/session",
                headers={
                    "Authorization": config.auth_header,
                    "Content-Type": "application/json",
                },
                json={},
            )

    @pytest.mark.asyncio
    async def test_create_session_auth_error(self, config):
        """Test session creation with authentication error."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock 401 response
            mock_response = Mock()
            mock_response.status_code = 401
            mock_response.text = "Unauthorized"
            error = httpx.HTTPStatusError("401", request=Mock(), response=mock_response)
            mock_client.post.side_effect = error

            client = SpecSmithAPIClient(config)
            client.client = mock_client

            with pytest.raises(ValueError, match="Invalid API credentials"):
                await client.create_session()

    @pytest.mark.asyncio
    async def test_create_session_not_found_error(self, config):
        """Test session creation with 404 error."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock 404 response
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Not Found"
            error = httpx.HTTPStatusError("404", request=Mock(), response=mock_response)
            mock_client.post.side_effect = error

            client = SpecSmithAPIClient(config)
            client.client = mock_client

            with pytest.raises(ValueError, match="API endpoint not found"):
                await client.create_session()

    @pytest.mark.asyncio
    async def test_create_session_generic_error(self, config):
        """Test session creation with generic HTTP error."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock 500 response
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            error = httpx.HTTPStatusError("500", request=Mock(), response=mock_response)
            mock_client.post.side_effect = error

            client = SpecSmithAPIClient(config)
            client.client = mock_client

            with pytest.raises(ValueError, match="API error: 500"):
                await client.create_session()

    @pytest.mark.asyncio
    async def test_send_message_success(self, config):
        """Test successful message sending with streaming response."""
        # Create mock chunks with JSON data
        json_chunks = [
            '{"type": "message", "content": "Hello"}\n',
            '{"type": "message", "content": "World"}\n',
            '{"type": "file_action", "filename": "test.py"}\n',
        ]

        async def mock_aiter_text():
            for chunk in json_chunks:
                yield chunk

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Create mock response
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.aiter_text = mock_aiter_text
            mock_response.raise_for_status = Mock()

            # Create async context manager using asynccontextmanager
            @asynccontextmanager
            async def mock_stream(*args, **kwargs):
                yield mock_response

            mock_client.stream = mock_stream

            client = SpecSmithAPIClient(config)
            client.client = mock_client

            # Collect all yielded actions
            actions = []
            async for action in client.send_message("test-session", "Hello"):
                actions.append(action)

            assert len(actions) == 3
            assert actions[0] == {"type": "message", "content": "Hello"}
            assert actions[1] == {"type": "message", "content": "World"}
            assert actions[2] == {"type": "file_action", "filename": "test.py"}

    @pytest.mark.asyncio
    async def test_send_message_invalid_json(self, debug_config):
        """Test message sending with invalid JSON in response."""

        async def mock_aiter_text():
            yield '{"type": "message", "content": "Valid"}\n'
            yield "invalid json\n"
            yield '{"type": "message", "content": "Also valid"}\n'

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Create mock response
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.aiter_text = mock_aiter_text
            mock_response.raise_for_status = Mock()

            # Create async context manager using asynccontextmanager
            @asynccontextmanager
            async def mock_stream(*args, **kwargs):
                yield mock_response

            mock_client.stream = mock_stream

            client = SpecSmithAPIClient(debug_config)
            client.client = mock_client

            # Collect all yielded actions (should skip invalid JSON)
            actions = []
            async for action in client.send_message("test-session", "Hello"):
                actions.append(action)

            assert len(actions) == 2
            assert actions[0] == {"type": "message", "content": "Valid"}
            assert actions[1] == {"type": "message", "content": "Also valid"}

    @pytest.mark.asyncio
    async def test_send_message_session_not_found(self, config):
        """Test message sending with session not found error."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock 404 response
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.text = "Session not found"
            error = httpx.HTTPStatusError("404", request=Mock(), response=mock_response)

            # Create async context manager that raises error
            @asynccontextmanager
            async def mock_stream(*args, **kwargs):
                raise error
                yield  # This won't be reached

            mock_client.stream = mock_stream

            client = SpecSmithAPIClient(config)
            client.client = mock_client

            with pytest.raises(ValueError, match="Session not found: test-session"):
                async for _ in client.send_message("test-session", "Hello"):
                    pass

    @pytest.mark.asyncio
    async def test_test_connection_success(self, config):
        """Test successful connection test."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock successful health check
            health_response = Mock()
            health_response.status_code = 200

            # Mock successful auth check
            auth_response = Mock()
            auth_response.status_code = 200

            mock_client.get.side_effect = [health_response, auth_response]

            client = SpecSmithAPIClient(config)
            client.client = mock_client

            result = await client.test_connection()

            assert result is True
            assert mock_client.get.call_count == 2
            mock_client.get.assert_any_call("http://localhost:8000/agent/health")
            mock_client.get.assert_any_call(
                "http://localhost:8000/agent/auth",
                headers={"Authorization": config.auth_header},
            )

    @pytest.mark.asyncio
    async def test_test_connection_health_failure(self, config):
        """Test connection test with health check failure."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock failed health check
            health_response = Mock()
            health_response.status_code = 500
            mock_client.get.return_value = health_response

            client = SpecSmithAPIClient(config)
            client.client = mock_client

            result = await client.test_connection()

            assert result is False
            # Should only call health check, not auth check
            assert mock_client.get.call_count == 1

    @pytest.mark.asyncio
    async def test_test_connection_auth_failure(self, config):
        """Test connection test with auth failure."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            # Mock successful health check
            health_response = Mock()
            health_response.status_code = 200

            # Mock failed auth check
            auth_response = Mock()
            auth_response.status_code = 401
            auth_error = httpx.HTTPStatusError(
                "401", request=Mock(), response=auth_response
            )

            mock_client.get.side_effect = [health_response, auth_error]

            client = SpecSmithAPIClient(config)
            client.client = mock_client

            result = await client.test_connection()

            assert result is False

    @pytest.mark.asyncio
    async def test_context_manager(self, config):
        """Test using the client as an async context manager."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            async with SpecSmithAPIClient(config) as client:
                assert isinstance(client, SpecSmithAPIClient)
                assert client.client == mock_client

            # Should call aclose when exiting context
            mock_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_aclose(self, config):
        """Test manual client closing."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client

            client = SpecSmithAPIClient(config)
            client.client = mock_client

            await client.aclose()

            mock_client.aclose.assert_called_once()


class TestCheckAPIHealth:
    """Test cases for the synchronous health check function."""

    def test_check_api_health_success(self):
        """Test successful health check."""
        with patch("httpx.Client") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value.__enter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response

            result = check_api_health("http://localhost:8000")

            assert result is True
            mock_client.get.assert_called_once_with(
                "http://localhost:8000/agent/health"
            )

    def test_check_api_health_failure(self):
        """Test failed health check."""
        with patch("httpx.Client") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value.__enter__.return_value = mock_client

            mock_response = Mock()
            mock_response.status_code = 500
            mock_client.get.return_value = mock_response

            result = check_api_health("http://localhost:8000")

            assert result is False

    def test_check_api_health_exception(self):
        """Test health check with exception."""
        with patch("httpx.Client") as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value.__enter__.return_value = mock_client

            mock_client.get.side_effect = httpx.ConnectError("Connection failed")

            result = check_api_health("http://localhost:8000")

            assert result is False
