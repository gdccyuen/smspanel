"""Tests for the queue status API endpoint."""

def test_queue_status_endpoint_exists(app):
    """Queue status endpoint should return queue statistics."""
    with app.test_client() as client:
        response = client.get("/api/queue/status")
        assert response.status_code == 200
        data = response.get_json()
        assert "queue_depth" in data
        assert "msgs_per_sec" in data
        assert "pending_messages" in data
