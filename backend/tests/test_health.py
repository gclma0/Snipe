from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_health_endpoint_returns_service_status() -> None:
    app = create_app(
        Settings(
            app_name="Test API",
            app_version="0.0.0-test",
            environment="test",
            enable_docs=False,
        )
    )
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Test API",
        "version": "0.0.0-test",
        "environment": "test",
    }
