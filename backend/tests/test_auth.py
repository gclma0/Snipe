from datetime import UTC, datetime, timedelta

import jwt
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

TEST_SECRET = "test-secret-with-at-least-thirty-two-bytes"


def create_token(secret: str, subject: str = "00000000-0000-0000-0000-000000000001") -> str:
    now = datetime.now(tz=UTC)
    return jwt.encode(
        {
            "aud": "authenticated",
            "email": "candidate@example.com",
            "exp": now + timedelta(minutes=15),
            "iat": now,
            "role": "authenticated",
            "sub": subject,
        },
        secret,
        algorithm="HS256",
    )


def test_auth_me_rejects_missing_token() -> None:
    app = create_app(Settings(supabase_jwt_secret=TEST_SECRET))
    client = TestClient(app)

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_auth_me_rejects_unconfigured_jwt_secret() -> None:
    app = create_app(Settings(supabase_url=None, supabase_jwt_secret=None))
    client = TestClient(app)
    token = create_token(TEST_SECRET)

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 503


def test_auth_me_returns_authenticated_user() -> None:
    secret = TEST_SECRET
    app = create_app(Settings(supabase_url=None, supabase_jwt_secret=secret))
    client = TestClient(app)
    token = create_token(secret)

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == {
        "id": "00000000-0000-0000-0000-000000000001",
        "email": "candidate@example.com",
        "role": "authenticated",
    }
