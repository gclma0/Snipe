from datetime import UTC, datetime
from typing import Any

from fastapi import Depends

from app.auth.dependencies import get_current_user
from app.profile.schemas import EvidenceCandidate
from app.supabase.client import SupabaseClient
from app.supabase.dependencies import get_supabase_client

CurrentUser = Depends(get_current_user)
Supabase = Depends(get_supabase_client)

MAX_RESUME_BYTES = 8 * 1024 * 1024


def create_evidence(
    supabase: SupabaseClient,
    evidence: list[EvidenceCandidate],
) -> list[dict[str, Any]]:
    return supabase.create_profile_evidence(
        [
            {
                "profile_id": item.location_json["profile_id"],
                "source_id": item.location_json["source_id"],
                "fact_type": item.fact_type,
                "fact_key": item.fact_key,
                "excerpt": item.excerpt,
                "normalized_value": item.normalized_value,
                "confidence": item.confidence,
                "location_json": item.location_json,
            }
            for item in evidence
        ]
    )


def update_optional_source(
    *,
    supabase: SupabaseClient,
    profile: dict[str, Any],
    profile_id: str,
    user_id: str,
    source_key: str,
    value: dict[str, Any],
) -> dict[str, Any]:
    normalized_json = profile.get("normalized_json") or {}
    optional_sources = normalized_json.setdefault("optional_sources", {})
    optional_sources[source_key] = value
    next_version = int(profile.get("version") or 1) + 1
    return supabase.update_candidate_profile(
        profile_id=profile_id,
        user_id=user_id,
        payload={
            "version": next_version,
            "normalized_json": normalized_json,
            "updated_at": datetime.now(tz=UTC).isoformat(),
        },
    )
