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
