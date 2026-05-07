from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_metrics_endpoint():
    with TestClient(app) as client:
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
        assert b"# HELP" in response.content or b"# TYPE" in response.content


def test_openapi_includes_admin_and_internal_routes():
    with TestClient(app) as client:
        spec = client.get("/openapi.json").json()

    paths = set(spec["paths"].keys())

    assert "/api/admin/keywords" in paths
    assert "/api/admin/tasks" in paths
    assert "/api/admin/tasks/crawl" in paths
    assert "/api/admin/tasks/update" in paths
    assert "/api/admin/videos" in paths
    assert "/api/internal/videos" in paths
    assert "/api/internal/stats/keywords" in paths or any(
        p.startswith("/api/internal/stats") for p in paths
    )


def test_protected_endpoints_require_api_key():
    with TestClient(app) as client:
        response = client.get("/api/admin/tasks")
        assert response.status_code == 403


def test_app_metadata():
    assert app.title == "Vigor Server"
    assert app.version == "0.1.0"
