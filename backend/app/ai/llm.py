import json
from typing import Any

import httpx
from pydantic import BaseModel, Field, ValidationError

from app.core.config import Settings


class AIRecommendation(BaseModel):
    title: str
    rationale: str
    action: str
    priority: str = Field(pattern="^(high|medium|low)$")


class AIInterpretationResult(BaseModel):
    output_type: str = "ai_readiness_interpretation"
    output_version: str = "ai-readiness-interpretation-v1"
    provider: str
    model_name: str
    summary: str
    readiness_explanation: str
    recommendations: list[AIRecommendation] = Field(min_length=1, max_length=6)
    cautions: list[str] = Field(default_factory=list, max_length=5)
    cached: bool = False


class AIProviderError(RuntimeError):
    pass


class AIClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.provider = (settings.ai_provider or "local_template").strip() or "local_template"
        self.model_name = settings.ai_model or "local-template-v1"

    def generate_interpretation(self, context: dict[str, Any]) -> AIInterpretationResult:
        if self.provider == "local_template":
            return _local_template_interpretation(context)
        if self.provider in {"openai_compatible", "openai"}:
            return self._openai_compatible_interpretation(context)
        raise AIProviderError(f"Unsupported AI_PROVIDER: {self.provider}.")

    def _openai_compatible_interpretation(self, context: dict[str, Any]) -> AIInterpretationResult:
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
                    "content": json.dumps(
                        {
                            "task": (
                                "Create a concise readiness explanation and prioritized "
                                "recommendations."
                            ),
                            "context": context,
                        },
                        sort_keys=True,
                    ),
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
            content = response.json()["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return AIInterpretationResult(
                provider=self.provider,
                model_name=self.model_name,
                **parsed,
            )
        except (KeyError, TypeError, ValueError, ValidationError) as exc:
            raise AIProviderError("AI provider returned an invalid structured response.") from exc


def _local_template_interpretation(context: dict[str, Any]) -> AIInterpretationResult:
    readiness = context["readiness"]
    skill_gap = context.get("skill_gap") or {}
    missing = skill_gap.get("missing") or []
    matched = skill_gap.get("matched") or []
    specialization = readiness.get("primary_specialization") or "the target career area"
    recommendations = [
        AIRecommendation(
            title="Strengthen the highest-impact gaps",
            rationale=(
                "The current profile has measurable readiness signals, but the target role still "
                "has unmatched requirements."
            ),
            action=(
                f"Prioritize evidence for {', '.join(missing[:3])}."
                if missing
                else "Add stronger proof for the most important target-role requirements."
            ),
            priority="high",
        ),
        AIRecommendation(
            title="Make verified strengths easier to scan",
            rationale=(
                "Recruiters and ATS systems benefit from repeated, consistent skill evidence."
            ),
            action=(
                f"Keep {', '.join(matched[:4])} visible in the resume, profile, and "
                "project evidence."
                if matched
                else "Move the strongest verified skills into the summary and skills sections."
            ),
            priority="medium",
        ),
    ]
    return AIInterpretationResult(
        provider="local_template",
        model_name="local-template-v1",
        summary=(
            f"The profile is currently scoring {readiness['overall']}/100 for "
            f"{specialization} readiness."
        ),
        readiness_explanation=(
            "Snipe is combining deterministic resume quality, ATS readiness, profile completeness, "
            "and job-specific skill alignment signals. This interpretation uses compact structured "
            "profile data only."
        ),
        recommendations=recommendations,
        cautions=[
            (
                "Do not add skills, metrics, or achievements unless they are supported by "
                "real evidence."
            )
        ],
    )
