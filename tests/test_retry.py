"""Tests for retry logic."""
import pytest


def test_tenacity_available():
    """Tenacity library should be available for retry logic."""
    import tenacity
    assert tenacity is not None
    # Check version has retry decorator
    assert hasattr(tenacity, "retry")
    assert hasattr(tenacity, "stop_after_attempt")
    assert hasattr(tenacity, "wait_exponential")
