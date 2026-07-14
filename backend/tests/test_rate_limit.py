from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.request_context import REQUEST_ID_HEADER
from app.main import create_app


def test_public_health_endpoint_is_rate_limited_with_retry_headers() -> None:
    app = create_app(
        Settings(
            enable_docs=False,
            public_rate_limit_requests=2,
            public_rate_limit_window_seconds=60,
        )
    )
    client = TestClient(app)

    assert client.get("/api/v1/health").status_code == 200
    second = client.get("/api/v1/health")
    limited = client.get("/api/v1/health")

    assert second.headers["X-RateLimit-Limit"] == "2"
    assert second.headers["X-RateLimit-Remaining"] == "0"
    assert limited.status_code == 429
    assert limited.json()["detail"] == "Rate limit exceeded. Try again later."
    assert limited.headers["Retry-After"]
    assert limited.headers["X-RateLimit-Limit"] == "2"
    assert limited.headers["X-RateLimit-Remaining"] == "0"
    assert limited.headers[REQUEST_ID_HEADER]


def test_rate_limit_uses_path_specific_buckets() -> None:
    app = create_app(
        Settings(
            enable_docs=False,
            public_rate_limit_requests=1,
            public_rate_limit_window_seconds=60,
        )
    )
    client = TestClient(app)

    assert client.get("/api/v1/health").status_code == 200
    assert client.get("/api/v1/health").status_code == 429
    assert client.get("/api/v1/health/ai-provider").status_code == 200


def test_rate_limit_can_be_disabled_for_local_testing() -> None:
    app = create_app(
        Settings(
            enable_docs=False,
            public_rate_limit_enabled=False,
            public_rate_limit_requests=1,
            public_rate_limit_window_seconds=60,
        )
    )
    client = TestClient(app)

    assert client.get("/api/v1/health").status_code == 200
    assert client.get("/api/v1/health").status_code == 200


def test_rate_limit_does_not_apply_to_authenticated_profile_routes() -> None:
    app = create_app(
        Settings(
            enable_docs=False,
            public_rate_limit_requests=1,
            public_rate_limit_window_seconds=60,
            supabase_jwt_secret="test-secret-with-at-least-thirty-two-bytes",
        )
    )
    client = TestClient(app)

    first = client.get("/api/v1/profiles")
    second = client.get("/api/v1/profiles")

    assert first.status_code == 401
    assert second.status_code == 401
