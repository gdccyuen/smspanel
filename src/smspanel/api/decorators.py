"""API request validation decorators."""

from functools import wraps
from typing import Callable

from flask import request
from .responses import bad_request


def validate_json(required_fields: list[str] | None = None):
    """Decorator to validate JSON request body has required fields.

    Args:
        required_fields: List of required field names.

    Returns:
        Decorator function.
    """

    def decorator(f: Callable):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json()
            if not data:
                return bad_request("Request body must be valid JSON", "INVALID_JSON")

            if required_fields:
                missing_fields = [
                    field for field in required_fields if field not in data or not data[field]
                ]
                if missing_fields:
                    return bad_request(
                        f"Missing required field(s): {', '.join(missing_fields)}",
                        "MISSING_FIELDS",
                    )

            return f(*args, **kwargs)

        return decorated_function

    return decorator
