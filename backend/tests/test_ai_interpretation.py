from dataclasses import dataclass, field
from typing import Any

from fastapi.testclient import TestClient

from app.ai.context import build_ai_interpretation_context
from app.ai.interview import build_interview_prep_context
from app.ai.llm import (
    AIClient,
    AIInterpretationResult,
    AIRecommendation,
    InterviewPrepResult,
    InterviewQuestion,
    KeywordInsertionRecommendation,
    ProjectRecommendation,
    ProjectRoadmapResult,
    ResumeRewriteResult,
    ResumeRewriteSuggestion,
    ResumeTailoringPackageResult,
    RoadmapStep,
)
from app.ai.resume_rewrite import build_resume_rewrite_context
from app.ai.roadmap import build_project_roadmap_context
from app.ai.tailoring import build_resume_tailoring_context
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
    tailoring_prompts: list[dict[str, Any]] = []
    interview_prompts: list[dict[str, Any]] = []
    roadmap_prompts: list[dict[str, Any]] = []

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

    def generate_resume_tailoring_package(
        self,
        context: dict[str, Any],
    ) -> ResumeTailoringPackageResult:
        self.tailoring_prompts.append(context)
        return ResumeTailoringPackageResult(
            provider="fake",
            model_name="fake-model",
            summary="Tailoring package is evidence-bound.",
            tailored_summary="Operations analyst with verified Excel, SQL, and operations signals.",
            skill_order=["excel", "sql", "operations"],
            keyword_recommendations=[
                KeywordInsertionRecommendation(
                    keyword="excel",
                    placement="skills section",
                    reason="Verified and relevant.",
                    evidence_status="verified",
                )
            ],
            missing_evidence_warnings=["Add communication only if supported by real evidence."],
            cautions=["Do not invent unsupported skills."],
        )

    def generate_interview_prep(
        self,
        context: dict[str, Any],
    ) -> InterviewPrepResult:
        self.interview_prompts.append(context)
        return InterviewPrepResult(
            provider="fake",
            model_name="fake-model",
            summary="Interview prep is evidence-bound.",
            questions=[
                InterviewQuestion(
                    category="role_specific",
                    question="How would you approach the Operations Analyst role?",
                    why_it_matters="Tests role understanding.",
                    answer_guidance="Use only verified Excel, SQL, and operations examples.",
                    evidence_to_use=["excel", "sql", "operations"],
                )
            ],
            star_guidance=["Situation: use a real context.", "Result: use a true outcome."],
            missing_evidence_warnings=[
                "Add communication only if supported by real evidence."
            ],
            cautions=["Do not invent unsupported stories."],
        )

    def generate_project_roadmap(
        self,
        context: dict[str, Any],
    ) -> ProjectRoadmapResult:
        self.roadmap_prompts.append(context)
        return ProjectRoadmapResult(
            provider="fake",
            model_name="fake-model",
            summary="Project roadmap is evidence-bound.",
            projects=[
                ProjectRecommendation(
                    title="Operations dashboard case study",
                    objective="Build future proof for verified Excel and SQL skills.",
                    skills_practiced=["excel", "sql", "operations"],
                    deliverables=["case study", "dashboard notes"],
                    evidence_to_add=["project link"],
                )
            ],
            roadmap=[
                RoadmapStep(
                    timeframe="7_day",
                    focus="Scope one realistic project.",
                    actions=["Choose a project tied to verified skills."],
                    success_criteria=["scope is documented"],
                )
            ],
            missing_evidence_warnings=[
                "Add communication only if supported by real evidence."
            ],
            cautions=["Do not present recommended projects as completed."],
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


def profile_without_skills() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "sources": [{"source_id": "source-id"}],
        "sections": {
            "summary": "Candidate summary without explicit skill keywords.",
            "experience": "Helped the team complete weekly work.",
        },
        "skills": [],
    }


def client_with_fake_supabase(fake: FakeSupabaseClient, monkeypatch) -> TestClient:
    import app.api.routes.ai as ai_route

    FakeAIClient.prompts = []
    FakeAIClient.rewrite_prompts = []
    FakeAIClient.tailoring_prompts = []
    FakeAIClient.interview_prompts = []
    FakeAIClient.roadmap_prompts = []
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


def test_local_resume_rewrite_does_not_return_noop_suggestions() -> None:
    readiness = build_readiness_dashboard(normalized_profile(), structured_job())
    context = build_resume_rewrite_context(
        normalized_profile=normalized_profile(),
        readiness=readiness,
        structured_job=structured_job(),
    )

    result = AIClient(
        Settings(supabase_url=None, supabase_jwt_secret=TEST_SECRET)
    ).generate_resume_rewrite_suggestions(context)

    assert result.suggestions
    assert all(item.suggested != item.original for item in result.suggestions)


def test_local_resume_rewrite_alternate_mode_changes_suggestion() -> None:
    readiness = build_readiness_dashboard(normalized_profile(), structured_job())
    context = build_resume_rewrite_context(
        normalized_profile=normalized_profile(),
        readiness=readiness,
        structured_job=structured_job(),
    )
    default_result = AIClient(
        Settings(supabase_url=None, supabase_jwt_secret=TEST_SECRET)
    ).generate_resume_rewrite_suggestions(context)

    alternate_context = {**context, "generation_mode": "alternate"}
    alternate_result = AIClient(
        Settings(supabase_url=None, supabase_jwt_secret=TEST_SECRET)
    ).generate_resume_rewrite_suggestions(alternate_context)

    assert default_result.suggestions[0].suggested != alternate_result.suggestions[0].suggested


def test_local_resume_rewrite_alternate_mode_changes_no_evidence_placeholder() -> None:
    context = {
        "existing_bullets": ["Managed weekly reporting updates."],
        "verified_skills": [],
        "target_job": None,
        "skill_gap": None,
    }
    default_result = AIClient(
        Settings(supabase_url=None, supabase_jwt_secret=TEST_SECRET)
    ).generate_resume_rewrite_suggestions(context)

    alternate_context = {**context, "generation_mode": "alternate"}
    alternate_result = AIClient(
        Settings(supabase_url=None, supabase_jwt_secret=TEST_SECRET)
    ).generate_resume_rewrite_suggestions(alternate_context)

    assert default_result.summary != alternate_result.summary
    assert default_result.suggestions[0].suggested != alternate_result.suggestions[0].suggested


def test_local_interpretation_alternate_mode_changes_summary() -> None:
    readiness = build_readiness_dashboard(normalized_profile(), structured_job())
    context = build_ai_interpretation_context(
        normalized_profile=normalized_profile(),
        readiness=readiness,
        structured_job=structured_job(),
    )
    default_result = AIClient(
        Settings(supabase_url=None, supabase_jwt_secret=TEST_SECRET)
    ).generate_interpretation(context)

    alternate_context = {**context, "generation_mode": "alternate"}
    alternate_result = AIClient(
        Settings(supabase_url=None, supabase_jwt_secret=TEST_SECRET)
    ).generate_interpretation(alternate_context)

    assert default_result.summary != alternate_result.summary
    assert default_result.recommendations[0].title != alternate_result.recommendations[0].title


def test_local_interpretation_explains_missing_skill_evidence() -> None:
    readiness = build_readiness_dashboard(profile_without_skills(), structured_job())
    context = build_ai_interpretation_context(
        normalized_profile=profile_without_skills(),
        readiness=readiness,
        structured_job=structured_job(),
    )

    result = AIClient(
        Settings(supabase_url=None, supabase_jwt_secret=TEST_SECRET)
    ).generate_interpretation(context)

    assert "did not find verified skills" in result.summary.lower()
    assert "major resume" in result.recommendations[0].rationale.lower()
    assert "do not add skills you cannot support" in result.recommendations[1].action.lower()


def test_local_resume_rewrite_explains_missing_skill_evidence() -> None:
    readiness = build_readiness_dashboard(profile_without_skills(), structured_job())
    context = build_resume_rewrite_context(
        normalized_profile=profile_without_skills(),
        readiness=readiness,
        structured_job=structured_job(),
    )

    result = AIClient(
        Settings(supabase_url=None, supabase_jwt_secret=TEST_SECRET)
    ).generate_resume_rewrite_suggestions(context)

    assert "no verified skills were found" in result.summary.lower()
    assert "add only real skills" in result.cautions[0].lower()


def test_resume_tailoring_context_excludes_raw_resume_sections() -> None:
    readiness = build_readiness_dashboard(normalized_profile(), structured_job())
    context = build_resume_tailoring_context(
        normalized_profile=normalized_profile(),
        readiness=readiness,
        structured_job=structured_job(),
    )

    assert "RAW_UNIQUE_RESUME_PHRASE" not in str(context)
    assert "RAW_UNIQUE_EXPERIENCE_PHRASE" not in str(context)
    assert context["verified_skills"] == ["excel", "operations", "project management", "sql"]


def test_local_resume_tailoring_warns_about_missing_evidence() -> None:
    readiness = build_readiness_dashboard(profile_without_skills(), structured_job())
    context = build_resume_tailoring_context(
        normalized_profile=profile_without_skills(),
        readiness=readiness,
        structured_job=structured_job(),
    )

    result = AIClient(
        Settings(supabase_url=None, supabase_jwt_secret=TEST_SECRET)
    ).generate_resume_tailoring_package(context)

    assert "limited" in result.summary.lower()
    assert result.missing_evidence_warnings
    assert result.keyword_recommendations[0].evidence_status == "missing_evidence"


def test_local_resume_tailoring_alternate_mode_changes_package() -> None:
    readiness = build_readiness_dashboard(normalized_profile(), structured_job())
    context = build_resume_tailoring_context(
        normalized_profile=normalized_profile(),
        readiness=readiness,
        structured_job=structured_job(),
    )
    default_result = AIClient(
        Settings(supabase_url=None, supabase_jwt_secret=TEST_SECRET)
    ).generate_resume_tailoring_package(context)

    alternate_context = {**context, "generation_mode": "alternate"}
    alternate_result = AIClient(
        Settings(supabase_url=None, supabase_jwt_secret=TEST_SECRET)
    ).generate_resume_tailoring_package(alternate_context)

    assert default_result.summary != alternate_result.summary
    assert default_result.tailored_summary != alternate_result.tailored_summary


def test_interview_prep_context_excludes_raw_resume_sections() -> None:
    readiness = build_readiness_dashboard(normalized_profile(), structured_job())
    context = build_interview_prep_context(
        normalized_profile=normalized_profile(),
        readiness=readiness,
        structured_job=structured_job(),
    )

    assert "RAW_UNIQUE_RESUME_PHRASE" not in str(context)
    assert len(context["experience_signals"]) <= 5
    assert all(len(item) <= 220 for item in context["experience_signals"])
    assert context["verified_skills"] == ["excel", "operations", "project management", "sql"]


def test_local_interview_prep_warns_about_missing_evidence() -> None:
    readiness = build_readiness_dashboard(profile_without_skills(), structured_job())
    context = build_interview_prep_context(
        normalized_profile=profile_without_skills(),
        readiness=readiness,
        structured_job=structured_job(),
    )

    result = AIClient(
        Settings(supabase_url=None, supabase_jwt_secret=TEST_SECRET)
    ).generate_interview_prep(context)

    assert "limited" in result.summary.lower()
    assert result.star_guidance
    assert "no verified skills" in result.missing_evidence_warnings[0].lower()
    assert all("invent" not in item.question.lower() for item in result.questions)


def test_local_interview_prep_alternate_mode_changes_questions() -> None:
    readiness = build_readiness_dashboard(normalized_profile(), structured_job())
    context = build_interview_prep_context(
        normalized_profile=normalized_profile(),
        readiness=readiness,
        structured_job=structured_job(),
    )
    default_result = AIClient(
        Settings(supabase_url=None, supabase_jwt_secret=TEST_SECRET)
    ).generate_interview_prep(context)

    alternate_context = {**context, "generation_mode": "alternate"}
    alternate_result = AIClient(
        Settings(supabase_url=None, supabase_jwt_secret=TEST_SECRET)
    ).generate_interview_prep(alternate_context)

    assert default_result.summary != alternate_result.summary
    assert default_result.questions[0].question != alternate_result.questions[0].question


def test_project_roadmap_context_excludes_raw_resume_sections() -> None:
    readiness = build_readiness_dashboard(normalized_profile(), structured_job())
    context = build_project_roadmap_context(
        normalized_profile=normalized_profile(),
        readiness=readiness,
        structured_job=structured_job(),
    )

    assert "RAW_UNIQUE_RESUME_PHRASE" not in str(context)
    assert len(context["experience_signals"]) <= 5
    assert all(len(item) <= 220 for item in context["experience_signals"])
    assert context["verified_skills"] == ["excel", "operations", "project management", "sql"]


def test_local_project_roadmap_warns_about_missing_evidence() -> None:
    readiness = build_readiness_dashboard(profile_without_skills(), structured_job())
    context = build_project_roadmap_context(
        normalized_profile=profile_without_skills(),
        readiness=readiness,
        structured_job=structured_job(),
    )

    result = AIClient(
        Settings(supabase_url=None, supabase_jwt_secret=TEST_SECRET)
    ).generate_project_roadmap(context)

    assert "limited" in result.summary.lower()
    assert len(result.projects) == 3
    assert {step.timeframe for step in result.roadmap} == {"7_day", "30_day", "90_day"}
    assert "no verified skills" in result.missing_evidence_warnings[0].lower()
    assert "future work" in result.cautions[0].lower()


def test_local_project_roadmap_alternate_mode_changes_summary() -> None:
    readiness = build_readiness_dashboard(normalized_profile(), structured_job())
    context = build_project_roadmap_context(
        normalized_profile=normalized_profile(),
        readiness=readiness,
        structured_job=structured_job(),
    )
    default_result = AIClient(
        Settings(supabase_url=None, supabase_jwt_secret=TEST_SECRET)
    ).generate_project_roadmap(context)

    alternate_context = {**context, "generation_mode": "alternate"}
    alternate_result = AIClient(
        Settings(supabase_url=None, supabase_jwt_secret=TEST_SECRET)
    ).generate_project_roadmap(alternate_context)

    assert default_result.summary != alternate_result.summary
    assert default_result.projects[0].title != alternate_result.projects[0].title


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


def test_resume_rewrite_force_regenerate_bypasses_cached_output(monkeypatch) -> None:
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
        json={"job_description_id": TEST_JOB_ID, "force_regenerate": True},
    )

    assert response.status_code == 201
    assert response.json()["cached"] is False
    assert response.json()["summary"] == "Rewrite suggestions are evidence-bound."
    assert fake.outputs
    assert FakeAIClient.rewrite_prompts[0]["generation_mode"] == "alternate"


def test_interpretation_force_regenerate_bypasses_cached_output(monkeypatch) -> None:
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
        json={"job_description_id": TEST_JOB_ID, "force_regenerate": True},
    )

    assert response.status_code == 201
    assert response.json()["cached"] is False
    assert (
        response.json()["summary"]
        == "Candidate is ready for the target role with focused improvements."
    )
    assert fake.outputs
    assert FakeAIClient.prompts[0]["generation_mode"] == "alternate"


def test_resume_tailoring_endpoint_generates_and_persists(monkeypatch) -> None:
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
        f"/api/v1/profiles/{TEST_PROFILE_ID}/ai/resume-tailoring-package",
        json={"job_description_id": TEST_JOB_ID},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["provider"] == "fake"
    assert body["skill_order"] == ["excel", "sql", "operations"]
    assert fake.outputs[0]["output_type"] == "ai_resume_tailoring_package"
    assert "RAW_UNIQUE_RESUME_PHRASE" not in str(FakeAIClient.tailoring_prompts[0])


def test_resume_tailoring_endpoint_returns_cached_output(monkeypatch) -> None:
    cached_result = ResumeTailoringPackageResult(
        provider="fake",
        model_name="fake-model",
        summary="Cached tailoring.",
        tailored_summary="Cached summary.",
        skill_order=["excel"],
        keyword_recommendations=[],
        missing_evidence_warnings=[],
        cautions=[],
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
        f"/api/v1/profiles/{TEST_PROFILE_ID}/ai/resume-tailoring-package",
        json={"job_description_id": TEST_JOB_ID},
    )

    assert response.status_code == 201
    assert response.json()["cached"] is True
    assert response.json()["summary"] == "Cached tailoring."
    assert fake.outputs == []
    assert FakeAIClient.tailoring_prompts == []


def test_interview_prep_endpoint_generates_and_persists(monkeypatch) -> None:
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
        f"/api/v1/profiles/{TEST_PROFILE_ID}/ai/interview-prep",
        json={"job_description_id": TEST_JOB_ID},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["provider"] == "fake"
    assert body["questions"][0]["category"] == "role_specific"
    assert fake.outputs[0]["output_type"] == "ai_interview_prep"
    assert "RAW_UNIQUE_RESUME_PHRASE" not in str(FakeAIClient.interview_prompts[0])


def test_interview_prep_endpoint_returns_cached_output(monkeypatch) -> None:
    cached_result = InterviewPrepResult(
        provider="fake",
        model_name="fake-model",
        summary="Cached interview prep.",
        questions=[
            InterviewQuestion(
                category="behavioral",
                question="Cached question?",
                why_it_matters="Cached reason.",
                answer_guidance="Cached guidance.",
                evidence_to_use=["excel"],
            )
        ],
        star_guidance=[],
        missing_evidence_warnings=[],
        cautions=[],
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
        f"/api/v1/profiles/{TEST_PROFILE_ID}/ai/interview-prep",
        json={"job_description_id": TEST_JOB_ID},
    )

    assert response.status_code == 201
    assert response.json()["cached"] is True
    assert response.json()["summary"] == "Cached interview prep."
    assert fake.outputs == []
    assert FakeAIClient.interview_prompts == []


def test_interview_prep_force_regenerate_bypasses_cached_output(monkeypatch) -> None:
    cached_result = InterviewPrepResult(
        provider="fake",
        model_name="fake-model",
        summary="Cached interview prep.",
        questions=[],
        star_guidance=[],
        missing_evidence_warnings=[],
        cautions=[],
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
        f"/api/v1/profiles/{TEST_PROFILE_ID}/ai/interview-prep",
        json={"job_description_id": TEST_JOB_ID, "force_regenerate": True},
    )

    assert response.status_code == 201
    assert response.json()["cached"] is False
    assert response.json()["summary"] == "Interview prep is evidence-bound."
    assert fake.outputs
    assert FakeAIClient.interview_prompts[0]["generation_mode"] == "alternate"


def test_project_roadmap_endpoint_generates_and_persists(monkeypatch) -> None:
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
        f"/api/v1/profiles/{TEST_PROFILE_ID}/ai/project-roadmap-recommendations",
        json={"job_description_id": TEST_JOB_ID},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["provider"] == "fake"
    assert body["projects"][0]["title"] == "Operations dashboard case study"
    assert fake.outputs[0]["output_type"] == "ai_project_roadmap_recommendations"
    assert "RAW_UNIQUE_RESUME_PHRASE" not in str(FakeAIClient.roadmap_prompts[0])


def test_project_roadmap_endpoint_returns_cached_output(monkeypatch) -> None:
    cached_result = ProjectRoadmapResult(
        provider="fake",
        model_name="fake-model",
        summary="Cached project roadmap.",
        projects=[],
        roadmap=[],
        missing_evidence_warnings=[],
        cautions=[],
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
        f"/api/v1/profiles/{TEST_PROFILE_ID}/ai/project-roadmap-recommendations",
        json={"job_description_id": TEST_JOB_ID},
    )

    assert response.status_code == 201
    assert response.json()["cached"] is True
    assert response.json()["summary"] == "Cached project roadmap."
    assert fake.outputs == []
    assert FakeAIClient.roadmap_prompts == []


def test_project_roadmap_force_regenerate_bypasses_cached_output(monkeypatch) -> None:
    cached_result = ProjectRoadmapResult(
        provider="fake",
        model_name="fake-model",
        summary="Cached project roadmap.",
        projects=[],
        roadmap=[],
        missing_evidence_warnings=[],
        cautions=[],
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
        f"/api/v1/profiles/{TEST_PROFILE_ID}/ai/project-roadmap-recommendations",
        json={"job_description_id": TEST_JOB_ID, "force_regenerate": True},
    )

    assert response.status_code == 201
    assert response.json()["cached"] is False
    assert response.json()["summary"] == "Project roadmap is evidence-bound."
    assert fake.outputs
    assert FakeAIClient.roadmap_prompts[0]["generation_mode"] == "alternate"
