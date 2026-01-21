"""Tests for logging utilities."""

import pytest

from smspanel.utils.logging import (
    clear_request_id,
    generate_request_id,
    get_request_id,
    log_error,
    set_request_id,
)


@pytest.fixture(autouse=True)
def cleanup_request_id():
    """Clean up request ID context after each test."""
    yield
    clear_request_id()


def test_logging_module_exists():
    """Logging utility module should exist."""
    from smspanel.utils.logging import (
        log_error,
        log_request,
        setup_app_logging,
        generate_request_id,
        get_request_id,
    )

    assert log_error is not None
    assert log_request is not None
    assert setup_app_logging is not None
    assert generate_request_id is not None
    assert get_request_id is not None


def test_generate_request_id():
    """generate_request_id should return a string."""
    request_id = generate_request_id()
    assert isinstance(request_id, str)
    assert len(request_id) > 0


def test_get_request_id_default():
    """get_request_id should return N/A when no request context."""
    result = get_request_id()
    assert result == "N/A"


def test_set_and_get_request_id():
    """set_request_id and get_request_id should work together."""
    test_id = "test-1234"
    set_request_id(test_id)
    assert get_request_id() == test_id


def test_log_error_function():
    """log_error should handle errors without raising."""
    set_request_id("test-request")
    try:
        raise ValueError("Test error for logging")
    except ValueError as e:
        # Should not raise
        log_error(e, {"extra": "data"})
