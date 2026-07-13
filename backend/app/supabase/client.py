from typing import Any
from urllib.parse import quote

import httpx

from app.core.config import Settings


class SupabaseError(RuntimeError):
    def __init__(self, message: str, *, operation: str = "supabase") -> None:
        super().__init__(message)
        self.operation = operation


class SupabaseClient:
    def __init__(self, settings: Settings) -> None:
        if not settings.supabase_url or not settings.supabase_service_role_key:
            raise SupabaseError("Supabase URL and service role key are required.")
        self.settings = settings
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
            raise SupabaseError(
                f"Profile ownership check failed: {response.text[:300]}",
                operation="ownership_check",
            )
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
                    "select": "id,user_id,version,career_goal,preferred_role,normalized_json",
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

    def create_analysis(self, payload: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(timeout=15, trust_env=False) as client:
            response = client.post(
                f"{self.base_url}/rest/v1/analyses",
                headers={
                    **self.headers,
                    "Content-Type": "application/json",
                    "Prefer": "return=representation",
                },
                json=payload,
            )
        if response.status_code >= 400:
            raise SupabaseError(f"Analysis insert failed: {response.text[:300]}")
        rows = response.json()
        return rows[0] if rows else payload

    def create_job_description(self, payload: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(timeout=15, trust_env=False) as client:
            response = client.post(
                f"{self.base_url}/rest/v1/job_descriptions",
                headers={
                    **self.headers,
                    "Content-Type": "application/json",
                    "Prefer": "return=representation",
                },
                json=payload,
            )
        if response.status_code >= 400:
            raise SupabaseError(f"Job description insert failed: {response.text[:300]}")
        rows = response.json()
        return rows[0] if rows else payload

    def get_job_description(
        self,
        *,
        job_description_id: str,
        profile_id: str,
        user_id: str,
    ) -> dict[str, Any] | None:
        with httpx.Client(timeout=15, trust_env=False) as client:
            response = client.get(
                f"{self.base_url}/rest/v1/job_descriptions",
                headers=self.headers,
                params={
                    "select": "id,user_id,profile_id,structured_json,input_hash",
                    "id": f"eq.{job_description_id}",
                    "profile_id": f"eq.{profile_id}",
                    "user_id": f"eq.{user_id}",
                    "limit": "1",
                },
            )
        if response.status_code >= 400:
            raise SupabaseError(f"Job description fetch failed: {response.text[:300]}")
        rows = response.json()
        return rows[0] if rows else None

    def list_job_descriptions(
        self,
        *,
        profile_id: str,
        user_id: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        with httpx.Client(timeout=15, trust_env=False) as client:
            response = client.get(
                f"{self.base_url}/rest/v1/job_descriptions",
                headers=self.headers,
                params={
                    "select": (
                        "id,user_id,profile_id,source_type,input_hash,"
                        "structured_json,created_at"
                    ),
                    "profile_id": f"eq.{profile_id}",
                    "user_id": f"eq.{user_id}",
                    "order": "created_at.desc",
                    "limit": str(limit),
                },
            )
        if response.status_code >= 400:
            raise SupabaseError(f"Job descriptions list failed: {response.text[:300]}")
        return response.json()

    def create_generated_output(self, payload: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(timeout=15, trust_env=False) as client:
            response = client.post(
                f"{self.base_url}/rest/v1/generated_outputs",
                headers={
                    **self.headers,
                    "Content-Type": "application/json",
                    "Prefer": "return=representation",
                },
                json=payload,
            )
        if response.status_code >= 400:
            raise SupabaseError(f"Generated output insert failed: {response.text[:300]}")
        rows = response.json()
        return rows[0] if rows else payload

    def get_generated_output(
        self,
        *,
        user_id: str,
        profile_id: str,
        output_type: str,
        input_hash: str,
        job_description_id: str | None = None,
    ) -> dict[str, Any] | None:
        params = {
            "select": "id,result_json,result_markdown,provider,model_name,created_at",
            "user_id": f"eq.{user_id}",
            "profile_id": f"eq.{profile_id}",
            "output_type": f"eq.{output_type}",
            "input_hash": f"eq.{input_hash}",
            "job_description_id": (
                f"eq.{job_description_id}" if job_description_id else "is.null"
            ),
            "status": "eq.completed",
            "order": "created_at.desc",
            "limit": "1",
        }
        with httpx.Client(timeout=15, trust_env=False) as client:
            response = client.get(
                f"{self.base_url}/rest/v1/generated_outputs",
                headers=self.headers,
                params=params,
            )
        if response.status_code >= 400:
            raise SupabaseError(f"Generated output fetch failed: {response.text[:300]}")
        rows = response.json()
        return rows[0] if rows else None

    def list_generated_outputs(
        self,
        *,
        user_id: str,
        profile_id: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        with httpx.Client(timeout=15, trust_env=False) as client:
            response = client.get(
                f"{self.base_url}/rest/v1/generated_outputs",
                headers=self.headers,
                params={
                    "select": (
                        "id,output_type,job_description_id,prompt_version,provider,"
                        "model_name,result_json,result_markdown,status,created_at"
                    ),
                    "user_id": f"eq.{user_id}",
                    "profile_id": f"eq.{profile_id}",
                    "status": "eq.completed",
                    "order": "created_at.desc",
                    "limit": str(limit),
                },
            )
        if response.status_code >= 400:
            raise SupabaseError(f"Generated output list failed: {response.text[:300]}")
        return response.json()

    def get_generated_output_by_id(
        self,
        *,
        user_id: str,
        profile_id: str,
        output_id: str,
    ) -> dict[str, Any] | None:
        with httpx.Client(timeout=15, trust_env=False) as client:
            response = client.get(
                f"{self.base_url}/rest/v1/generated_outputs",
                headers=self.headers,
                params={
                    "select": (
                        "id,output_type,job_description_id,prompt_version,provider,"
                        "model_name,result_json,result_markdown,status,created_at"
                    ),
                    "id": f"eq.{output_id}",
                    "user_id": f"eq.{user_id}",
                    "profile_id": f"eq.{profile_id}",
                    "status": "eq.completed",
                    "limit": "1",
                },
            )
        if response.status_code >= 400:
            raise SupabaseError(f"Generated output fetch failed: {response.text[:300]}")
        rows = response.json()
        return rows[0] if rows else None

    def delete_generated_output(
        self,
        *,
        user_id: str,
        profile_id: str,
        output_id: str,
    ) -> bool:
        with httpx.Client(timeout=15, trust_env=False) as client:
            response = client.delete(
                f"{self.base_url}/rest/v1/generated_outputs",
                headers={
                    **self.headers,
                    "Prefer": "return=representation",
                },
                params={
                    "id": f"eq.{output_id}",
                    "user_id": f"eq.{user_id}",
                    "profile_id": f"eq.{profile_id}",
                },
            )
        if response.status_code >= 400:
            raise SupabaseError(f"Generated output delete failed: {response.text[:300]}")
        return bool(response.json())

    def create_rag_document(self, payload: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(timeout=15, trust_env=False) as client:
            response = client.post(
                f"{self.base_url}/rest/v1/rag_documents",
                headers={
                    **self.headers,
                    "Content-Type": "application/json",
                    "Prefer": "return=representation",
                },
                json=payload,
            )
        if response.status_code >= 400:
            raise SupabaseError(f"RAG document insert failed: {response.text[:300]}")
        rows = response.json()
        return rows[0] if rows else payload

    def create_rag_chunks(self, payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not payloads:
            return []
        with httpx.Client(timeout=30, trust_env=False) as client:
            response = client.post(
                f"{self.base_url}/rest/v1/rag_chunks",
                headers={
                    **self.headers,
                    "Content-Type": "application/json",
                    "Prefer": "return=representation",
                },
                json=payloads,
            )
        if response.status_code >= 400:
            raise SupabaseError(f"RAG chunk insert failed: {response.text[:300]}")
        return response.json()

    def list_rag_documents(
        self,
        *,
        user_id: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        with httpx.Client(timeout=15, trust_env=False) as client:
            response = client.get(
                f"{self.base_url}/rest/v1/rag_documents",
                headers=self.headers,
                params={
                    "select": (
                        "id,title,source_type,source_url,content_hash,"
                        "embedding_model,metadata,created_at"
                    ),
                    "user_id": f"eq.{user_id}",
                    "order": "created_at.desc",
                    "limit": str(limit),
                },
            )
        if response.status_code >= 400:
            raise SupabaseError(f"RAG document list failed: {response.text[:300]}")
        return response.json()

    def delete_rag_document(
        self,
        *,
        user_id: str,
        document_id: str,
    ) -> bool:
        with httpx.Client(timeout=15, trust_env=False) as client:
            response = client.delete(
                f"{self.base_url}/rest/v1/rag_documents",
                headers={
                    **self.headers,
                    "Prefer": "return=representation",
                },
                params={
                    "id": f"eq.{document_id}",
                    "user_id": f"eq.{user_id}",
                },
            )
        if response.status_code >= 400:
            raise SupabaseError(f"RAG document delete failed: {response.text[:300]}")
        return bool(response.json())

    def match_rag_chunks(
        self,
        *,
        user_id: str,
        query_embedding: list[float],
        source_types: list[str],
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        with httpx.Client(timeout=15, trust_env=False) as client:
            response = client.post(
                f"{self.base_url}/rest/v1/rpc/match_rag_chunks",
                headers={
                    **self.headers,
                    "Content-Type": "application/json",
                },
                json={
                    "match_user_id": user_id,
                    "query_embedding": query_embedding,
                    "source_types": source_types,
                    "match_count": limit,
                },
            )
        if response.status_code >= 400:
            raise SupabaseError(f"RAG chunk match failed: {response.text[:300]}")
        return response.json()

    def list_profile_storage_paths(self, profile_id: str, user_id: str) -> list[str]:
        with httpx.Client(timeout=15, trust_env=False) as client:
            response = client.get(
                f"{self.base_url}/rest/v1/profile_sources",
                headers=self.headers,
                params={
                    "select": "storage_path",
                    "profile_id": f"eq.{profile_id}",
                    "user_id": f"eq.{user_id}",
                    "storage_path": "not.is.null",
                },
            )
        if response.status_code >= 400:
            raise SupabaseError(
                f"Storage path list failed: {response.text[:300]}",
                operation="storage_path_list",
            )
        return [row["storage_path"] for row in response.json() if row.get("storage_path")]

    def delete_storage_objects(self, paths: list[str]) -> None:
        if not paths:
            return
        with httpx.Client(timeout=30, trust_env=False) as client:
            response = client.request(
                "DELETE",
                f"{self.base_url}/storage/v1/object/{self.storage_bucket}",
                headers={
                    **self.headers,
                    "Content-Type": "application/json",
                },
                json={"prefixes": paths},
            )
        if response.status_code == 404:
            return
        if response.status_code >= 400:
            raise SupabaseError(
                f"Storage object delete failed: {response.text[:300]}",
                operation="storage_delete",
            )

    def delete_candidate_profile(self, profile_id: str, user_id: str) -> bool:
        with httpx.Client(timeout=15, trust_env=False) as client:
            response = client.delete(
                f"{self.base_url}/rest/v1/candidate_profiles",
                headers={
                    **self.headers,
                    "Prefer": "return=representation",
                },
                params={"id": f"eq.{profile_id}", "user_id": f"eq.{user_id}"},
            )
        if response.status_code >= 400:
            raise SupabaseError(
                f"Profile delete failed: {response.text[:300]}",
                operation="profile_delete",
            )
        return bool(response.json())

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
