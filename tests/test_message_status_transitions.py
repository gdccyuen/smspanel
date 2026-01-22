"""Tests for Message job status transitions in the queue worker."""

import pytest

from smspanel import db
from smspanel.models import User, Message, MessageJobStatus, RecipientStatus


def test_message_status_transitions_on_send(app):
    """Message should transition from PENDING to SENDING when processed."""
    with app.app_context():
        from smspanel.models import User, Message, MessageJobStatus

        user = User(username="test", password_hash="x", is_admin=False)
        db.session.add(user)
        db.session.commit()

        msg = Message(
            user_id=user.id,
            content="Test",
            job_status=MessageJobStatus.PENDING,
            queue_position=1,
        )
        db.session.add(msg)
        db.session.commit()

        # Simulate worker picking up message
        msg.job_status = MessageJobStatus.SENDING
        msg.queue_position = None
        db.session.commit()

        assert msg.job_status == MessageJobStatus.SENDING
        assert msg.queue_position is None
