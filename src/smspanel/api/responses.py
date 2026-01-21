"""API response utilities for standardized error and success responses."""

from flask import jsonify
from typing import Any


class APIResponse:
    """Standardized API response builder."""

    @staticmethod
    def success(data: Any = None, message: str | None = None, status_code: int = 200) -> tuple:
        """Return a success response.

        Args:
            data: The response data.
            message: Optional success message.
            status_code: HTTP status code (default: 200).

        Returns:
            JSON response tuple.
        """
        response_dict: dict[str, Any] = {"success": True}
        if data is not None:
            response_dict["data"] = data
        if message:
            response_dict["message"] = message
        return jsonify(response_dict), status_code

    @staticmethod
    def error(message: str, status_code: int = 400, error_code: str | None = None) -> tuple:
        """Return an error response.

        New format:
        {
            "error": {
                "code": "ERROR_CODE",
                "message": "Human-readable error message"
            }
        }

        Args:
            message: Error message.
            status_code: HTTP status code (default: 400).
            error_code: Optional machine-readable error code.

        Returns:
            JSON error response tuple.
        """
        error_dict: dict[str, Any] = {"message": message}
        if error_code:
            error_dict["code"] = error_code

        return jsonify({"error": error_dict}), status_code


# Common error responses
def unauthorized(message: str = "Unauthorized", error_code: str = "UNAUTHORIZED") -> tuple:
    """Return unauthorized error (401)."""
    return APIResponse.error(message, 401, error_code)


def bad_request(message: str = "Bad request", error_code: str = "BAD_REQUEST") -> tuple:
    """Return bad request error (400)."""
    return APIResponse.error(message, 400, error_code)


def not_found(message: str = "Resource not found", error_code: str = "NOT_FOUND") -> tuple:
    """Return not found error (404)."""
    return APIResponse.error(message, 404, error_code)


def service_unavailable(
    message: str = "Service is busy, please try again later",
    error_code: str = "SERVICE_UNAVAILABLE",
) -> tuple:
    """Return service unavailable error (503)."""
    return APIResponse.error(message, 503, error_code)


def internal_server_error(
    message: str = "Internal server error", error_code: str = "INTERNAL_SERVER_ERROR"
) -> tuple:
    """Return internal server error (500)."""
    return APIResponse.error(message, 500, error_code)
