from dataclasses import dataclass
from typing import Any

import httpx
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError

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

    signing_key = _fetch_signing_key(
        jwks_url=f"{issuer}/.well-known/jwks.json",
        key_id=header.get("kid"),
    )
    return jwt.decode(
        token,
        signing_key,
        algorithms=["ES256", "RS256"],
        audience="authenticated",
        issuer=issuer,
    )


def _fetch_signing_key(jwks_url: str, key_id: str | None) -> Any:
    if not key_id:
        raise InvalidTokenError("JWT key id is missing.")
    try:
        with httpx.Client(timeout=10, trust_env=False) as client:
            response = client.get(jwks_url)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise InvalidTokenError("Could not fetch Supabase JWKS.") from exc

    keys = response.json().get("keys")
    if not isinstance(keys, list):
        raise InvalidTokenError("Supabase JWKS is malformed.")

    for key in keys:
        if isinstance(key, dict) and key.get("kid") == key_id:
            return jwt.PyJWK.from_dict(key).key
    raise InvalidTokenError("JWT signing key was not found.")


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
