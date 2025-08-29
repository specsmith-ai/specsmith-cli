"""API client for communicating with the Specsmith Agent API."""

import json
from typing import Any, AsyncGenerator, Dict

import httpx
from rich.console import Console

from .config import Config


class SpecSmithAPIClient:
    """Client for communicating with the Specsmith Agent API."""

    def __init__(self, config: Config):
        self.config = config
        self.client = httpx.AsyncClient(timeout=300.0)  # 5 minute timeout
        self.console = Console()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def aclose(self):
        """Close the client."""
        await self.client.aclose()

    async def health_check(self) -> bool:
        """Check if the API is healthy."""
        try:
            response = await self.client.get(f"{self.config.api_url}/agent/health")
            return response.status_code == 200
        except Exception as e:
            if self.config.debug:
                self.console.print(f"[red]Health check failed: {e}[/red]")
            return False

    async def create_session(self) -> str:
        """Create a new session and return the session ID."""
        try:
            response = await self.client.post(
                f"{self.config.api_url}/agent/session",
                headers={
                    "Authorization": self.config.auth_header,
                    "Content-Type": "application/json",
                },
                json={},
            )
            response.raise_for_status()
            data = response.json()
            session_id = data["session_id"]
            return session_id
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ValueError(
                    "Invalid API credentials. Please check your access key ID and token."
                )
            elif e.response.status_code == 404:
                raise ValueError("API endpoint not found. Please check the API URL.")
            else:
                raise ValueError(
                    f"API error: {e.response.status_code} - {e.response.text}"
                )
        except Exception as e:
            raise ValueError(f"Failed to create session: {e}")

    async def send_message(
        self, session_id: str, content: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Send a message to the session and stream the response."""
        try:
            async with self.client.stream(
                "POST",
                f"{self.config.api_url}/agent/session/{session_id}/message",
                headers={
                    "Authorization": self.config.auth_header,
                    "Content-Type": "application/json",
                },
                json={"content": content},
            ) as response:
                response.raise_for_status()

                async for chunk in response.aiter_text():
                    if chunk.strip():
                        # Split by newlines in case multiple JSON objects are in one chunk
                        for line in chunk.split("\n"):
                            line = line.strip()
                            if line:
                                try:
                                    action = json.loads(line)
                                    yield action
                                except json.JSONDecodeError:
                                    if self.config.debug:
                                        self.console.print(
                                            f"[yellow]Failed to parse JSON: {line}[/yellow]"
                                        )
                                    continue

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ValueError(
                    "Invalid API credentials. Please check your access key ID and token."
                )
            elif e.response.status_code == 404:
                raise ValueError(f"Session not found: {session_id}")
            else:
                raise ValueError(
                    f"API error: {e.response.status_code} - {e.response.text}"
                )
        except Exception as e:
            raise ValueError(f"Failed to send message: {e}")

    async def test_connection(self) -> bool:
        """Test the connection to the API."""
        try:
            # First check health
            if not await self.health_check():
                return False

            # Then test authentication
            try:
                response = await self.client.get(
                    f"{self.config.api_url}/agent/auth",
                    headers={
                        "Authorization": self.config.auth_header,
                    },
                )
                response.raise_for_status()
                return True
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    if self.config.debug:
                        self.console.print("[red]Authentication failed[/red]")
                    return False
                else:
                    if self.config.debug:
                        self.console.print(
                            f"[red]Auth check failed: {e.response.status_code}[/red]"
                        )
                    return False

        except Exception as e:
            if self.config.debug:
                self.console.print(f"[red]Connection test failed: {e}[/red]")
            return False


def check_api_health(api_url: str) -> bool:
    """Check if the API is healthy (synchronous version)."""
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{api_url}/agent/health")
            return response.status_code == 200
    except Exception:
        return False
