"""Tests for MessageJobStatus enum and Message job tracking fields."""

from smspanel import db
from smspanel.models import MessageJobStatus


def test_message_job_status_enum():
    """Test MessageJobStatus enum values."""
    assert MessageJobStatus.PENDING == "pending"
    assert MessageJobStatus.SENDING == "sending"
    assert MessageJobStatus.COMPLETED == "completed"
    assert MessageJobStatus.PARTIAL == "partial"
    assert MessageJobStatus.FAILED == "failed"


def test_message_job_status_fields(app):
    """Test Message model has job_status fields with correct defaults."""
    with app.app_context():
        from smspanel.models import Message, MessageJobStatus
        msg = Message(user_id=1, content="Test")
        db.session.add(msg)
        db.session.flush()
        assert msg.job_status == MessageJobStatus.PENDING
        assert msg.queue_position is None
        assert msg.estimated_complete_at is None
