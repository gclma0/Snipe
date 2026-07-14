from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.supabase.client import SupabaseClient, SupabaseError
from app.supabase.dependencies import get_supabase_client

router = APIRouter(prefix="/usage", tags=["usage"])
Supabase = Depends(get_supabase_client)

MAX_METADATA_KEYS = 12
MAX_METADATA_STRING_LENGTH = 120
SENSITIVE_METADATA_KEYS = {
    "access_token",
    "ai_output",
    "api_key",
    "authorization",
    "content",
    "document",
    "email",
    "generated_output",
    "github_username",
    "job_text",
    "linkedin_url",
    "name",
    "phone",
    "portfolio_url",
    "profile_id",
    "raw_document",
    "raw_text",
    "resume",
    "resume_text",
    "secret",
    "token",
    "user_id",
}
SENSITIVE_KEY_FRAGMENTS = ("secret", "token", "email", "phone", "resume", "raw", "document")


class UsageEventRequest(BaseModel):
    anonymous_session_id: str = Field(min_length=8, max_length=128)
    event_name: str = Field(min_length=3, max_length=80, pattern=r"^[a-z][a-z0-9_]*$")
    surface: str = Field(min_length=2, max_length=80, pattern=r"^[a-z][a-z0-9_]*$")
    metadata: dict[str, Any] = Field(default_factory=dict)
    path: str | None = Field(default=None, max_length=120)

    @field_validator("metadata")
    @classmethod
    def metadata_must_be_dict(cls, value: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("metadata must be an object")
        return value


class UsageEventResponse(BaseModel):
    accepted: bool
    event_name: str


@router.post("/events", response_model=UsageEventResponse, status_code=status.HTTP_202_ACCEPTED)
def create_usage_event(
    request: UsageEventRequest,
    supabase: SupabaseClient = Supabase,
) -> UsageEventResponse:
    payload = {
        "anonymous_session_id": request.anonymous_session_id,
        "event_name": request.event_name,
        "surface": request.surface,
        "metadata": sanitize_metadata(request.metadata),
        "path": sanitize_path(request.path),
    }
    try:
        supabase.create_usage_event(payload)
    except SupabaseError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Supabase {exc.operation} failed.",
        ) from exc
    return UsageEventResponse(accepted=True, event_name=request.event_name)


def sanitize_metadata(metadata: dict[str, Any]) -> dict[str, str | int | float | bool | None]:
    sanitized: dict[str, str | int | float | bool | None] = {}
    for raw_key, raw_value in metadata.items():
        key = str(raw_key).strip().lower()
        if not key or len(sanitized) >= MAX_METADATA_KEYS or _is_sensitive_key(key):
            continue
        value = _sanitize_metadata_value(raw_value)
        if value is not None or raw_value is None:
            sanitized[key[:80]] = value
    return sanitized


def sanitize_path(path: str | None) -> str | None:
    if not path:
        return None
    clean_path = path.split("?", 1)[0].split("#", 1)[0].strip()
    return clean_path[:120] if clean_path else None


def _is_sensitive_key(key: str) -> bool:
    return key in SENSITIVE_METADATA_KEYS or any(fragment in key for fragment in SENSITIVE_KEY_FRAGMENTS)


def _sanitize_metadata_value(value: Any) -> str | int | float | bool | None:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int | float):
        return value
    if isinstance(value, str):
        return value.strip()[:MAX_METADATA_STRING_LENGTH]
    return None
