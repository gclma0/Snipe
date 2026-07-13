import json
from typing import Any

import httpx
from pydantic import ValidationError

from app.ai.schemas import (
    AIInterpretationResult,
    ApplicationMaterialsResult,
    InterviewPrepResult,
    LearningPlanResult,
    ProjectRoadmapResult,
    ResumeRewriteResult,
    ResumeTailoringPackageResult,
)
from app.core.config import Settings


class AIProviderError(RuntimeError):
    pass


class OpenAICompatibleProvider:
    def __init__(self, settings: Settings, provider: str, model_name: str) -> None:
        self.settings = settings
        self.provider = provider
        self.model_name = model_name

    def generate_interpretation(self, context: dict[str, Any]) -> AIInterpretationResult:
        parsed = self._request_json(
            task="Create a concise readiness explanation and prioritized recommendations.",
            context=context,
        )
        try:
            return AIInterpretationResult(
                provider=self.provider,
                model_name=self.model_name,
                **parsed,
            )
        except (TypeError, ValidationError) as exc:
            raise AIProviderError("AI provider returned an invalid structured response.") from exc

    def generate_resume_rewrite(self, context: dict[str, Any]) -> ResumeRewriteResult:
        parsed = self._request_json(
            task=(
                "Create evidence-bound resume rewrite suggestions. Do not invent metrics, "
                "achievements, employers, skills, or experience. If a stronger bullet needs a "
                "real metric, use a bracketed placeholder and set needs_candidate_value true."
            ),
            context=context,
        )
        try:
            return ResumeRewriteResult(
                provider=self.provider,
                model_name=self.model_name,
                **parsed,
            )
        except (TypeError, ValidationError) as exc:
            raise AIProviderError("AI provider returned an invalid structured response.") from exc

    def generate_resume_tailoring(self, context: dict[str, Any]) -> ResumeTailoringPackageResult:
        parsed = self._request_json(
            task=(
                "Create an evidence-bound resume tailoring package with a tailored summary, "
                "skill ordering, keyword placement recommendations, missing-evidence warnings, "
                "and cautions. Do not invent skills, achievements, metrics, employers, or "
                "experience."
            ),
            context=context,
        )
        try:
            return ResumeTailoringPackageResult(
                provider=self.provider,
                model_name=self.model_name,
                **parsed,
            )
        except (TypeError, ValidationError) as exc:
            raise AIProviderError("AI provider returned an invalid structured response.") from exc

    def generate_interview_prep(self, context: dict[str, Any]) -> InterviewPrepResult:
        parsed = self._request_json(
            task=(
                "Create evidence-bound interview preparation with role-specific, technical or "
                "profession-specific, behavioral, and screening questions. Include STAR answer "
                "guidance and missing-evidence warnings. Do not write fabricated answers or "
                "invent skills, achievements, metrics, employers, credentials, or experience."
            ),
            context=context,
        )
        try:
            return InterviewPrepResult(
                provider=self.provider,
                model_name=self.model_name,
                **parsed,
            )
        except (TypeError, ValidationError) as exc:
            raise AIProviderError("AI provider returned an invalid structured response.") from exc

    def generate_project_roadmap(self, context: dict[str, Any]) -> ProjectRoadmapResult:
        parsed = self._request_json(
            task=(
                "Create evidence-bound project recommendations and 7-day, 30-day, and 90-day "
                "roadmap steps. Recommend realistic future work only. Do not claim projects are "
                "completed and do not invent skills, achievements, metrics, employers, "
                "credentials, or experience."
            ),
            context=context,
        )
        try:
            return ProjectRoadmapResult(
                provider=self.provider,
                model_name=self.model_name,
                **parsed,
            )
        except (TypeError, ValidationError) as exc:
            raise AIProviderError("AI provider returned an invalid structured response.") from exc

    def generate_learning_plan(self, context: dict[str, Any]) -> LearningPlanResult:
        parsed = self._request_json(
            task=(
                "Create evidence-bound daily, weekly, and monthly learning plans. Each item "
                "must include tasks, practice activity, evidence to create, and success "
                "criteria. Do not invent skills, achievements, metrics, employers, "
                "credentials, or experience."
            ),
            context=context,
        )
        try:
            return LearningPlanResult(
                provider=self.provider,
                model_name=self.model_name,
                **parsed,
            )
        except (TypeError, ValidationError) as exc:
            raise AIProviderError("AI provider returned an invalid structured response.") from exc

    def generate_application_materials(self, context: dict[str, Any]) -> ApplicationMaterialsResult:
        parsed = self._request_json(
            task=(
                "Create evidence-bound application materials: a standard cover letter, concise "
                "cover note, and email application. Use candidate-review placeholders when "
                "details are missing. Do not invent skills, achievements, metrics, employers, "
                "credentials, or experience."
            ),
            context=context,
        )
        try:
            return ApplicationMaterialsResult(
                provider=self.provider,
                model_name=self.model_name,
                **parsed,
            )
        except (TypeError, ValidationError) as exc:
            raise AIProviderError("AI provider returned an invalid structured response.") from exc

    def _request_json(self, *, task: str, context: dict[str, Any]) -> dict[str, Any]:
        if not self.settings.ai_api_key:
            raise AIProviderError("AI_API_KEY is required for the configured AI provider.")
        base_url = (self.settings.ai_base_url or "https://api.openai.com/v1").rstrip("/")
        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are Snipe, a career assistant. Use only the compact structured "
                        "context provided. Do not invent achievements, metrics, skills, "
                        "employers, credentials, or experience. Return strict JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps({"task": task, "context": context}, sort_keys=True),
                },
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
        }
        with httpx.Client(timeout=self.settings.ai_timeout_seconds, trust_env=False) as client:
            response = client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.settings.ai_api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        if response.status_code >= 400:
            raise AIProviderError(f"AI provider request failed with status {response.status_code}.")
        try:
            return json.loads(response.json()["choices"][0]["message"]["content"])
        except (KeyError, TypeError, ValueError) as exc:
            raise AIProviderError("AI provider returned invalid JSON.") from exc
