from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.request_context import PROCESS_TIME_HEADER, REQUEST_ID_HEADER
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
    assert response.headers[REQUEST_ID_HEADER]
    assert float(response.headers[PROCESS_TIME_HEADER]) >= 0


def test_request_context_preserves_client_request_id() -> None:
    app = create_app(
        Settings(
            app_name="Test API",
            app_version="0.0.0-test",
            environment="test",
            enable_docs=False,
        )
    )
    client = TestClient(app)

    response = client.get("/api/v1/health", headers={REQUEST_ID_HEADER: "smoke-test-request"})

    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER] == "smoke-test-request"
    assert float(response.headers[PROCESS_TIME_HEADER]) >= 0


def test_request_context_replaces_oversized_request_id() -> None:
    app = create_app(
        Settings(
            app_name="Test API",
            app_version="0.0.0-test",
            environment="test",
            enable_docs=False,
        )
    )
    client = TestClient(app)

    response = client.get("/api/v1/health", headers={REQUEST_ID_HEADER: "x" * 200})

    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER] != "x" * 200
    assert len(response.headers[REQUEST_ID_HEADER]) == 32


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
    assert "AI_BASE_URL is required" in body["issues"][2]
    assert "secret" not in str(body).lower()


def test_ai_provider_health_reports_ready_external_configuration_without_key_value() -> None:
    app = create_app(
        Settings(
            app_name="Test API",
            app_version="0.0.0-test",
            environment="test",
            enable_docs=False,
            ai_provider=" OPENAI_COMPATIBLE ",
            ai_model="free-model",
            ai_api_key="real-test-key",
            ai_base_url="https://example.test/v1",
            ai_timeout_seconds=12,
        )
    )
    client = TestClient(app)

    response = client.get("/api/v1/health/ai-provider")

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "provider": "openai_compatible",
        "model_name": "free-model",
        "mode": "external",
        "configured": True,
        "requires_api_key": True,
        "api_key_configured": True,
        "base_url_configured": True,
        "timeout_seconds": 12,
        "issues": [],
    }
    assert "real-test-key" not in str(body)


def test_ai_provider_health_rejects_placeholder_key_and_invalid_base_url_without_key_value() -> None:
    app = create_app(
        Settings(
            app_name="Test API",
            app_version="0.0.0-test",
            environment="test",
            enable_docs=False,
            ai_provider="openai_compatible",
            ai_model="free-model",
            ai_api_key="your-api-key",
            ai_base_url="not-a-url",
        )
    )
    client = TestClient(app)

    response = client.get("/api/v1/health/ai-provider")

    assert response.status_code == 200
    body = response.json()
    assert body["configured"] is False
    assert body["api_key_configured"] is False
    assert "AI_API_KEY is required" in body["issues"][0]
    assert "AI_BASE_URL must be a valid http or https URL." in body["issues"][1]
    assert "your-api-key" not in str(body)


def test_ai_provider_health_reports_unsupported_provider() -> None:
    app = create_app(
        Settings(
            app_name="Test API",
            app_version="0.0.0-test",
            environment="test",
            enable_docs=False,
            ai_provider="paid_only_vendor",
            ai_model="model",
            ai_api_key="real-test-key",
        )
    )
    client = TestClient(app)

    response = client.get("/api/v1/health/ai-provider")

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "paid_only_vendor"
    assert body["mode"] == "unsupported"
    assert body["configured"] is False
    assert body["requires_api_key"] is False
    assert body["api_key_configured"] is True
    assert body["issues"] == ["Unsupported AI_PROVIDER: paid_only_vendor."]
    assert "real-test-key" not in str(body)
