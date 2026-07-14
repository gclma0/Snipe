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


def test_ai_provider_health_reports_local_template_without_secrets() -> None:
    app = create_app(
        Settings(
            app_name="Test API",
            app_version="0.0.0-test",
            environment="test",
            enable_docs=False,
        )
    )
    client = TestClient(app)

    response = client.get("/api/v1/health/ai-provider")

    assert response.status_code == 200
    assert response.json() == {
        "provider": "local_template",
        "model_name": "local-template-v1",
        "mode": "local_template",
        "configured": True,
        "requires_api_key": False,
        "api_key_configured": False,
        "base_url_configured": False,
        "timeout_seconds": 30,
        "issues": [],
    }


def test_ai_provider_health_reports_missing_external_configuration_without_key_value() -> None:
    app = create_app(
        Settings(
            app_name="Test API",
            app_version="0.0.0-test",
            environment="test",
            enable_docs=False,
            ai_provider="openai_compatible",
            ai_model="",
            ai_api_key=None,
        )
    )
    client = TestClient(app)

    response = client.get("/api/v1/health/ai-provider")

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "openai_compatible"
    assert body["mode"] == "external"
    assert body["configured"] is False
    assert body["requires_api_key"] is True
    assert body["api_key_configured"] is False
    assert "AI_API_KEY is required" in body["issues"][0]
    assert "AI_MODEL is required" in body["issues"][1]
    assert "secret" not in str(body).lower()
