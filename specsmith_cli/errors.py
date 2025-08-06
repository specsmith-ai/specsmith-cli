"""Error handling and sanitization for the Specsmith CLI."""

from enum import Enum
from typing import Optional


class ErrorType(Enum):
    """Types of errors that can occur."""

    CONNECTION_ERROR = "connection_error"
    AUTHENTICATION_ERROR = "authentication_error"
    SESSION_ERROR = "session_error"
    API_ERROR = "api_error"
    TIMEOUT_ERROR = "timeout_error"
    OVERLOADED_ERROR = "overloaded_error"
    UNKNOWN_ERROR = "unknown_error"


class SpecsmithError(Exception):
    """Base exception for Specsmith CLI errors."""

    def __init__(
        self, error_type: ErrorType, message: str, status_code: Optional[int] = None
    ):
        self.error_type = error_type
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def sanitize_error_message(error: Exception, debug: bool = False) -> str:
    """Sanitize error messages to avoid exposing internal details."""

    error_str = str(error).lower()

    # Connection and network errors
    if any(
        term in error_str
        for term in ["connection", "timeout", "network", "unreachable"]
    ):
        return "Unable to connect to the Specsmith API. Please check your internet connection and try again."

    # Authentication errors
    if any(
        term in error_str
        for term in ["401", "unauthorized", "invalid credentials", "authentication"]
    ):
        return "Authentication failed. Please check your API credentials."

    # Session errors
    if any(term in error_str for term in ["404", "not found", "session"]):
        return "Session not found. Please try starting a new chat session."

    # Overloaded/service busy errors
    if any(
        term in error_str
        for term in ["overloaded", "high demand", "busy", "rate limit"]
    ):
        return "The upstream AI service is currently experiencing high demand. Please try again in a few moments."

    # API errors
    if any(term in error_str for term in ["500", "502", "503", "504", "server error"]):
        return "The Specsmith API is temporarily unavailable. Please try again later."

    # Default sanitized message
    if debug:
        return f"An error occurred: {str(error)}"
    else:
        return "An unexpected error occurred. Please try again or contact support if the problem persists."


def create_error_from_exception(
    error: Exception, debug: bool = False
) -> SpecsmithError:
    """Create a sanitized SpecsmithError from any exception."""

    error_str = str(error).lower()

    # Determine error type
    if any(
        term in error_str
        for term in ["connection", "timeout", "network", "unreachable"]
    ):
        error_type = ErrorType.CONNECTION_ERROR
        status_code = None
    elif any(
        term in error_str
        for term in ["401", "unauthorized", "invalid credentials", "authentication"]
    ):
        error_type = ErrorType.AUTHENTICATION_ERROR
        status_code = 401
    elif any(term in error_str for term in ["404", "not found", "session"]):
        error_type = ErrorType.SESSION_ERROR
        status_code = 404
    elif any(
        term in error_str
        for term in ["overloaded", "high demand", "busy", "rate limit"]
    ):
        error_type = ErrorType.OVERLOADED_ERROR
        status_code = 429
    elif any(
        term in error_str for term in ["500", "502", "503", "504", "server error"]
    ):
        error_type = ErrorType.API_ERROR
        status_code = 500
    else:
        error_type = ErrorType.UNKNOWN_ERROR
        status_code = None

    message = sanitize_error_message(error, debug)
    return SpecsmithError(error_type, message, status_code)


def get_user_friendly_message(error: SpecsmithError) -> str:
    """Get a user-friendly message for display."""

    if error.error_type == ErrorType.CONNECTION_ERROR:
        return "❌ Connection Error\nUnable to connect to the Specsmith API.\n\n💡 Please check:\n• Your internet connection\n• The API URL in your config\n• That the API server is running"

    elif error.error_type == ErrorType.AUTHENTICATION_ERROR:
        return "❌ Authentication Error\nInvalid API credentials.\n\n💡 Please check:\n• Your access key ID\n• Your secret access token\n• That your credentials are correct"

    elif error.error_type == ErrorType.SESSION_ERROR:
        return "❌ Session Error\nUnable to find or access the chat session.\n\n💡 Please try:\n• Starting a new chat session\n• Checking your connection"

    elif error.error_type == ErrorType.OVERLOADED_ERROR:
        return "⚠️  Service Busy\nThe upstream AI service is currently experiencing high demand.\n\n💡 Please try again in a few moments."

    elif error.error_type == ErrorType.API_ERROR:
        return "❌ API Error\nThe Specsmith API is temporarily unavailable.\n\n💡 Please try again later."

    else:
        return f"❌ Unexpected Error\n{error.message}\n\n💡 Please try again or contact support if the problem persists."
