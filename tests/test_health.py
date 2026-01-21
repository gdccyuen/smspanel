"""Health check endpoint tests."""


def test_health_endpoint_exists(app):
    """Health check endpoint should exist."""
    with app.test_client() as client:
        response = client.get("/api/health")
        assert response.status_code in [200, 503]

        data = response.get_json()
        assert "status" in data
        assert data["status"] in ["healthy", "unhealthy"]


def test_health_endpoint_returns_details(app):
    """Health check should return system details."""
    with app.test_client() as client:
        response = client.get("/api/health")
        data = response.get_json()

        # Should include key health indicators
        assert "timestamp" in data
        assert "checks" in data
        assert "version" in data


def test_health_endpoint_database_check(app):
    """Health check should verify database connectivity."""
    with app.test_client() as client:
        response = client.get("/api/health")
        data = response.get_json()

        assert "database" in data["checks"]
        assert "healthy" in data["checks"]["database"]


def test_liveness_endpoint_exists(app):
    """Liveness probe endpoint should exist."""
    with app.test_client() as client:
        response = client.get("/api/health/live")
        assert response.status_code == 200

        data = response.get_json()
        assert data["status"] == "alive"


def test_readiness_endpoint_exists(app):
    """Readiness probe endpoint should exist."""
    with app.test_client() as client:
        response = client.get("/api/health/ready")
        assert response.status_code in [200, 503]

        data = response.get_json()
        assert "status" in data
