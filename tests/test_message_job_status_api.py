"""Tests for job status fields in message API endpoint."""

from smspanel import db
from smspanel.models import User, Message, Recipient, MessageJobStatus


def test_get_message_includes_job_status(app):
    """GET /api/sms/{id} should include job_status and queue info."""
    with app.app_context():
        user = User(username="test", password_hash="x", is_admin=False)
        user.token = User.generate_token()
        db.session.add(user)
        db.session.commit()

        msg = Message(
            user_id=user.id,
            content="Test message",
            job_status=MessageJobStatus.PENDING,
            queue_position=5,
        )
        db.session.add(msg)
        db.session.commit()

        with app.test_client() as client:
            response = client.get(f"/api/sms/{msg.id}", headers={"Authorization": f"Bearer {user.token}"})
            assert response.status_code == 200
            data = response.get_json()
            assert data["success"] is True
            assert "data" in data
            assert data["data"]["job_status"] == "pending"
            assert data["data"]["queue_position"] == 5
            assert "estimated_complete_at" in data["data"]
