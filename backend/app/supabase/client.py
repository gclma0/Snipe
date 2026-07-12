from typing import Any
from urllib.parse import quote

import httpx

from app.core.config import Settings


class SupabaseError(RuntimeError):
    pass


class SupabaseClient:
    def __init__(self, settings: Settings) -> None:
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise SupabaseError("Supabase URL and service role key are required.")
        self.base_url = settings.supabase_url.rstrip("/")
        self.service_role_key = settings.supabase_service_role_key
        self.storage_bucket = settings.supabase_storage_bucket

    @property
    def headers(self) -> dict[str, str]:
        return {
            "apikey": self.service_role_key,
            "Authorization": f"Bearer {self.service_role_key}",
        }

    def profile_belongs_to_user(self, profile_id: str, user_id: str) -> bool:
        with httpx.Client(timeout=15, trust_env=False) as client:
            response = client.get(
                f"{self.base_url}/rest/v1/candidate_profiles",
                headers=self.headers,
                params={
                    "select": "id",
                    "id": f"eq.{profile_id}",
                    "user_id": f"eq.{user_id}",
                    "limit": "1",
                },
            )
        if response.status_code >= 400:
            raise SupabaseError(f"Profile ownership check failed: {response.text[:300]}")
        return bool(response.json())

    def upload_document(
        self,
        path: str,
        content: bytes,
        content_type: str,
    ) -> None:
        object_path = quote(f"{self.storage_bucket}/{path}", safe="/")
        with httpx.Client(timeout=30, trust_env=False) as client:
            response = client.put(
                f"{self.base_url}/storage/v1/object/{object_path}",
                headers={
                    **self.headers,
                    "Content-Type": content_type,
                    "x-upsert": "false",
                },
                content=content,
            )
        if response.status_code >= 400:
            raise SupabaseError(f"Document upload failed: {response.text[:300]}")

    def create_profile_source(self, payload: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(timeout=15, trust_env=False) as client:
            response = client.post(
                f"{self.base_url}/rest/v1/profile_sources",
                headers={
                    **self.headers,
                    "Content-Type": "application/json",
                    "Prefer": "return=representation",
                },
                json=payload,
            )
        if response.status_code >= 400:
            raise SupabaseError(f"Source metadata insert failed: {response.text[:300]}")
        rows = response.json()
        return rows[0] if rows else payload

    def get_candidate_profile(self, profile_id: str, user_id: str) -> dict[str, Any] | None:
        with httpx.Client(timeout=15, trust_env=False) as client:
            response = client.get(
                f"{self.base_url}/rest/v1/candidate_profiles",
                headers=self.headers,
                params={
                    "select": "id,user_id,version,normalized_json",
                    "id": f"eq.{profile_id}",
                    "user_id": f"eq.{user_id}",
                    "limit": "1",
                },
            )
        if response.status_code >= 400:
            raise SupabaseError(f"Profile fetch failed: {response.text[:300]}")
        rows = response.json()
        return rows[0] if rows else None

    def update_candidate_profile(
        self,
        *,
        profile_id: str,
        user_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        with httpx.Client(timeout=15, trust_env=False) as client:
            response = client.patch(
                f"{self.base_url}/rest/v1/candidate_profiles",
                headers={
                    **self.headers,
                    "Content-Type": "application/json",
                    "Prefer": "return=representation",
                },
                params={"id": f"eq.{profile_id}", "user_id": f"eq.{user_id}"},
                json=payload,
            )
        if response.status_code >= 400:
            raise SupabaseError(f"Profile update failed: {response.text[:300]}")
        rows = response.json()
        return rows[0] if rows else payload

    def create_profile_evidence(self, payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not payloads:
            return []
        with httpx.Client(timeout=15, trust_env=False) as client:
            response = client.post(
                f"{self.base_url}/rest/v1/profile_evidence",
                headers={
                    **self.headers,
                    "Content-Type": "application/json",
                    "Prefer": "return=representation",
                },
                json=payloads,
            )
        if response.status_code >= 400:
            raise SupabaseError(f"Evidence insert failed: {response.text[:300]}")
        return response.json()

    def list_candidate_profiles(self, user_id: str) -> list[dict[str, Any]]:
        with httpx.Client(timeout=15, trust_env=False) as client:
            response = client.get(
                f"{self.base_url}/rest/v1/candidate_profiles",
                headers=self.headers,
                params={
                    "select": "id,career_goal,preferred_role,profile_status,created_at,updated_at",
                    "user_id": f"eq.{user_id}",
                    "order": "created_at.desc",
                },
            )
        if response.status_code >= 400:
            raise SupabaseError(f"Profile list failed: {response.text[:300]}")
        return response.json()

    def create_candidate_profile(self, payload: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(timeout=15, trust_env=False) as client:
            response = client.post(
                f"{self.base_url}/rest/v1/candidate_profiles",
                headers={
                    **self.headers,
                    "Content-Type": "application/json",
                    "Prefer": "return=representation",
                },
                json=payload,
            )
        if response.status_code >= 400:
            raise SupabaseError(f"Profile create failed: {response.text[:300]}")
        rows = response.json()
        return rows[0] if rows else payload
