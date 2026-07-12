from dataclasses import dataclass, field
from typing import Any

from fastapi.testclient import TestClient

from app.ai.context import build_ai_interpretation_context
from app.ai.llm import (
    AIInterpretationResult,
    AIRecommendation,
    ResumeRewriteResult,
    ResumeRewriteSuggestion,
)
from app.ai.resume_rewrite import build_resume_rewrite_context
from app.auth.dependencies import AuthenticatedUser, get_current_user
from app.core.config import Settings
from app.main import create_app
from app.scoring.readiness import build_readiness_dashboard
from app.supabase.dependencies import get_supabase_client

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_PROFILE_ID = "11111111-1111-1111-1111-111111111111"
TEST_JOB_ID = "22222222-2222-2222-2222-222222222222"
TEST_SECRET = "test-secret-with-at-least-thirty-two-bytes"


class FakeAIClient:
    prompts: list[dict[str, Any]] = []
    rewrite_prompts: list[dict[str, Any]] = []

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def generate_interpretation(self, context: dict[str, Any]) -> AIInterpretationResult:
        self.prompts.append(context)
        return AIInterpretationResult(
            provider="fake",
            model_name="fake-model",
            summary="Candidate is ready for the target role with focused improvements.",
            readiness_explanation="The score combines deterministic readiness signals.",
            recommendations=[
                AIRecommendation(
                    title="Close the main gap",
                    rationale="The target job requires one missing skill.",
                    action="Add real evidence for the missing requirement.",
                    priority="high",
                )
            ],
            cautions=["Do not invent unsupported achievements."],
        )

    def generate_resume_rewrite_suggestions(self, context: dict[str, Any]) -> ResumeRewriteResult:
        self.rewrite_prompts.append(context)
        return ResumeRewriteResult(
            provider="fake",
            model_name="fake-model",
            summary="Rewrite suggestions are evidence-bound.",
            suggestions=[
                ResumeRewriteSuggestion(
                    original="Led weekly operations reviews.",
                    suggested="Led weekly operations reviews using operations and SQL.",
                    rationale="Keeps the original fact and adds verified skills.",
                    evidence_used=["operations", "sql"],
                )
            ],
            cautions=["Do not invent unsupported metrics."],
        )


@dataclass
class FakeSupabaseClient:
    profile: dict[str, Any] | None
    job_description: dict[str, Any] | None = None
    cached_output: dict[str, Any] | None = None
    settings: Settings = field(
        default_factory=lambda: Settings(
            supabase_url=None,
            supabase_jwt_secret=TEST_SECRET,
            ai_provider="local_template",
        )
    )
    outputs: list[dict[str, Any]] = field(default_factory=list)

    def get_candidate_profile(self, profile_id: str, user_id: str) -> dict[str, Any] | None:
        if profile_id != TEST_PROFILE_ID or user_id != TEST_USER_ID:
            return None
        return self.profile

    def get_job_description(
        self,
        *,
        job_description_id: str,
        profile_id: str,
        user_id: str,
    ) -> dict[str, Any] | None:
        if (
            job_description_id != TEST_JOB_ID
            or profile_id != TEST_PROFILE_ID
            or user_id != TEST_USER_ID
        ):
            return None
        return self.job_description

    def get_generated_output(self, **kwargs) -> dict[str, Any] | None:
        return self.cached_output

    def create_generated_output(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = {"id": "output-id", **payload}
        self.outputs.append(row)
        return row


def normalized_profile() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "sources": [{"source_id": "source-id"}],
        "sections": {
            "summary": "RAW_UNIQUE_RESUME_PHRASE senior operations analyst with private detail.",
            "experience": "RAW_UNIQUE_EXPERIENCE_PHRASE led weekly reviews.",
            "skills": "Excel, SQL, operations, project management",
        },
        "skills": [
            {"name": "excel", "source": "resume"},
            {"name": "sql", "source": "resume"},
            {"name": "operations", "source": "resume"},
            {"name": "project management", "source": "resume"},
        ],
        "optional_sources": {
            "portfolio": {
                "technical_signals": [],
                "non_technical_signals": ["operations", "strategy"],
                "project_signal_count": 2,
                "contact_signal_count": 1,
            }
        },
    }


def structured_job() -> dict[str, Any]:
    return {
        "title": "Operations Analyst",
        "required_skills": ["Excel", "SQL", "communication"],
        "preferred_skills": ["project management"],
        "tools": [],
        "soft_skills": ["communication"],
        "ats_keywords": ["operations", "reporting"],
    }


def client_with_fake_supabase(fake: FakeSupabaseClient, monkeypatch) -> TestClient:
    import app.api.routes.ai as ai_route

    FakeAIClient.prompts = []
    FakeAIClient.rewrite_prompts = []
    monkeypatch.setattr(ai_route, "AIClient", FakeAIClient)
    app = create_app(Settings(supabase_url=None, supabase_jwt_secret=TEST_SECRET))
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        id=TEST_USER_ID,
        email="user@example.com",
        role="authenticated",
        claims={},
    )
    app.dependency_overrides[get_supabase_client] = lambda: fake
    return TestClient(app)


def test_compact_ai_context_excludes_raw_resume_sections() -> None:
    readiness = build_readiness_dashboard(normalized_profile(), structured_job())
    context = build_ai_interpretation_context(
        normalized_profile=normalized_profile(),
        readiness=readiness,
        structured_job=structured_job(),
    )

    assert "RAW_UNIQUE_RESUME_PHRASE" not in str(context)
    assert "RAW_UNIQUE_EXPERIENCE_PHRASE" not in str(context)
    assert context["skills"] == ["excel", "operations", "project management", "sql"]


def test_resume_rewrite_context_uses_bounded_existing_bullets() -> None:
    readiness = build_readiness_dashboard(normalized_profile(), structured_job())
    context = build_resume_rewrite_context(
        normalized_profile=normalized_profile(),
        readiness=readiness,
        structured_job=structured_job(),
    )

    assert "RAW_UNIQUE_RESUME_PHRASE" not in str(context)
    assert len(context["existing_bullets"]) <= 5
    assert all(len(item) <= 240 for item in context["existing_bullets"])


def test_ai_interpretation_endpoint_generates_and_persists(monkeypatch) -> None:
    fake = FakeSupabaseClient(
        profile={
            "id": TEST_PROFILE_ID,
            "user_id": TEST_USER_ID,
            "version": 4,
            "normalized_json": normalized_profile(),
        },
        job_description={
            "id": TEST_JOB_ID,
            "profile_id": TEST_PROFILE_ID,
            "user_id": TEST_USER_ID,
            "structured_json": structured_job(),
        },
    )
    client = client_with_fake_supabase(fake, monkeypatch)

    response = client.post(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/ai/readiness-interpretation",
        json={"job_description_id": TEST_JOB_ID},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["provider"] == "fake"
    assert body["cached"] is False
    assert fake.outputs[0]["output_type"] == "ai_readiness_interpretation"
    assert fake.outputs[0]["result_json"]["summary"] == body["summary"]
    assert "RAW_UNIQUE_RESUME_PHRASE" not in str(FakeAIClient.prompts[0])


def test_ai_interpretation_endpoint_returns_cached_output(monkeypatch) -> None:
    cached_result = AIInterpretationResult(
        provider="fake",
        model_name="fake-model",
        summary="Cached summary.",
        readiness_explanation="Cached explanation.",
        recommendations=[
            AIRecommendation(
                title="Cached recommendation",
                rationale="Cached rationale.",
                action="Cached action.",
                priority="medium",
            )
        ],
    )
    fake = FakeSupabaseClient(
        profile={
            "id": TEST_PROFILE_ID,
            "user_id": TEST_USER_ID,
            "version": 4,
            "normalized_json": normalized_profile(),
        },
        job_description={
            "id": TEST_JOB_ID,
            "profile_id": TEST_PROFILE_ID,
            "user_id": TEST_USER_ID,
            "structured_json": structured_job(),
        },
        cached_output={"result_json": cached_result.model_dump(exclude={"cached"})},
    )
    client = client_with_fake_supabase(fake, monkeypatch)

    response = client.post(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/ai/readiness-interpretation",
        json={"job_description_id": TEST_JOB_ID},
    )

    assert response.status_code == 201
    assert response.json()["cached"] is True
    assert response.json()["summary"] == "Cached summary."
    assert fake.outputs == []
    assert FakeAIClient.prompts == []


def test_resume_rewrite_endpoint_generates_and_persists(monkeypatch) -> None:
    fake = FakeSupabaseClient(
        profile={
            "id": TEST_PROFILE_ID,
            "user_id": TEST_USER_ID,
            "version": 4,
            "normalized_json": normalized_profile(),
        },
        job_description={
            "id": TEST_JOB_ID,
            "profile_id": TEST_PROFILE_ID,
            "user_id": TEST_USER_ID,
            "structured_json": structured_job(),
        },
    )
    client = client_with_fake_supabase(fake, monkeypatch)

    response = client.post(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/ai/resume-rewrite-suggestions",
        json={"job_description_id": TEST_JOB_ID},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["provider"] == "fake"
    assert body["suggestions"][0]["evidence_used"] == ["operations", "sql"]
    assert fake.outputs[0]["output_type"] == "ai_resume_rewrite_suggestions"
    assert "RAW_UNIQUE_RESUME_PHRASE" not in str(FakeAIClient.rewrite_prompts[0])


def test_resume_rewrite_endpoint_returns_cached_output(monkeypatch) -> None:
    cached_result = ResumeRewriteResult(
        provider="fake",
        model_name="fake-model",
        summary="Cached rewrite.",
        suggestions=[
            ResumeRewriteSuggestion(
                original="Original.",
                suggested="Suggested.",
                rationale="Cached.",
                evidence_used=["excel"],
            )
        ],
    )
    fake = FakeSupabaseClient(
        profile={
            "id": TEST_PROFILE_ID,
            "user_id": TEST_USER_ID,
            "version": 4,
            "normalized_json": normalized_profile(),
        },
        job_description={
            "id": TEST_JOB_ID,
            "profile_id": TEST_PROFILE_ID,
            "user_id": TEST_USER_ID,
            "structured_json": structured_job(),
        },
        cached_output={"result_json": cached_result.model_dump(exclude={"cached"})},
    )
    client = client_with_fake_supabase(fake, monkeypatch)

    response = client.post(
        f"/api/v1/profiles/{TEST_PROFILE_ID}/ai/resume-rewrite-suggestions",
        json={"job_description_id": TEST_JOB_ID},
    )

    assert response.status_code == 201
    assert response.json()["cached"] is True
    assert response.json()["summary"] == "Cached rewrite."
    assert fake.outputs == []
    assert FakeAIClient.rewrite_prompts == []
