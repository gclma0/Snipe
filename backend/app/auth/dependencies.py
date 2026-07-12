from dataclasses import dataclass
from typing import Any

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError, PyJWKClient

from app.core.config import Settings

bearer_scheme = HTTPBearer(auto_error=False)
BearerCredentials = Depends(bearer_scheme)


@dataclass(frozen=True)
class AuthenticatedUser:
    id: str
    email: str | None
    role: str | None
    claims: dict[str, Any]


def get_request_settings(request: Request) -> Settings:
    return request.app.state.settings


RequestSettings = Depends(get_request_settings)


def decode_supabase_token(token: str, settings: Settings) -> dict[str, Any]:
    header = jwt.get_unverified_header(token)
    issuer = f"{settings.supabase_url.rstrip('/')}/auth/v1" if settings.supabase_url else None

    if header.get("alg") == "HS256":
        if not settings.supabase_jwt_secret:
            raise InvalidTokenError("Supabase JWT secret is not configured.")
        return jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            audience="authenticated",
            issuer=issuer,
            options={"verify_iss": bool(issuer)},
        )

    if not issuer:
        raise InvalidTokenError("Supabase URL is not configured.")

    jwks_client = PyJWKClient(f"{issuer}/.well-known/jwks.json")
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["ES256", "RS256"],
        audience="authenticated",
        issuer=issuer,
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = BearerCredentials,
    settings: Settings = RequestSettings,
) -> AuthenticatedUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
        )

    if not settings.supabase_jwt_secret and not settings.supabase_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase JWT verification is not configured.",
        )

    try:
        claims = decode_supabase_token(credentials.credentials, settings)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token.",
        ) from exc

    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject is missing.",
        )

    return AuthenticatedUser(
        id=subject,
        email=claims.get("email"),
        role=claims.get("role"),
        claims=claims,
    )
