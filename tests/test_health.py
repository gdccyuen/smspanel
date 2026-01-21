"""Health check endpoint tests."""


def test_health_endpoint_exists():
    """Health check endpoint should exist."""
    from smspanel import create_app

    app = create_app()
    with app.test_client() as client:
        response = client.get("/api/health")
        assert response.status_code in [200, 503]

        data = response.get_json()
        assert "status" in data
        assert data["status"] in ["healthy", "unhealthy"]


def test_health_endpoint_returns_details():
    """Health check should return system details."""
    from smspanel import create_app

    app = create_app()
    with app.test_client() as client:
        response = client.get("/api/health")
        data = response.get_json()

        # Should include key health indicators
        assert "timestamp" in data
        assert "checks" in data
        assert "version" in data


def test_health_endpoint_database_check():
    """Health check should verify database connectivity."""
    from smspanel import create_app

    app = create_app()
    with app.test_client() as client:
        response = client.get("/api/health")
        data = response.get_json()

        assert "database" in data["checks"]
        assert "healthy" in data["checks"]["database"]


def test_liveness_endpoint_exists():
    """Liveness probe endpoint should exist."""
    from smspanel import create_app

    app = create_app()
    with app.test_client() as client:
        response = client.get("/api/health/live")
        assert response.status_code == 200

        data = response.get_json()
        assert data["status"] == "alive"


def test_readiness_endpoint_exists():
    """Readiness probe endpoint should exist."""
    from smspanel import create_app

    app = create_app()
    with app.test_client() as client:
        response = client.get("/api/health/ready")
        assert response.status_code in [200, 503]

        data = response.get_json()
        assert "status" in data
