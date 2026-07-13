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


class ResumeRewriteSuggestion(BaseModel):
    original: str
    suggested: str
    rationale: str
    evidence_used: list[str] = Field(default_factory=list, max_length=6)
    needs_candidate_value: bool = False


class ResumeRewriteResult(BaseModel):
    output_type: str = "ai_resume_rewrite_suggestions"
    output_version: str = "ai-resume-rewrite-suggestions-v1"
    provider: str
    model_name: str
    summary: str
    suggestions: list[ResumeRewriteSuggestion] = Field(default_factory=list, max_length=5)
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

    def generate_resume_rewrite_suggestions(self, context: dict[str, Any]) -> ResumeRewriteResult:
        if self.provider == "local_template":
            return _local_template_resume_rewrite(context)
        if self.provider in {"openai_compatible", "openai"}:
            return self._openai_compatible_resume_rewrite(context)
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

    def _openai_compatible_resume_rewrite(self, context: dict[str, Any]) -> ResumeRewriteResult:
        parsed = self._openai_compatible_json(
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

    def _openai_compatible_json(self, *, task: str, context: dict[str, Any]) -> dict[str, Any]:
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


def _local_template_interpretation(context: dict[str, Any]) -> AIInterpretationResult:
    readiness = context["readiness"]
    skill_gap = context.get("skill_gap") or {}
    generation_mode = context.get("generation_mode")
    missing = skill_gap.get("missing") or []
    matched = skill_gap.get("matched") or []
    specialization = readiness.get("primary_specialization") or "the target career area"
    if generation_mode == "alternate":
        recommendations = [
            AIRecommendation(
                title="Turn gaps into a short evidence plan",
                rationale=(
                    "The next improvement should focus on concrete proof for the requirements "
                    "that are not yet strongly represented."
                ),
                action=(
                    f"Create one real example for each of these areas: {', '.join(missing[:3])}."
                    if missing
                    else "Choose one target requirement and add a specific verified example for it."
                ),
                priority="high",
            ),
            AIRecommendation(
                title="Rebalance the profile around proven strengths",
                rationale=(
                    "The strongest existing signals should be repeated consistently across the "
                    "resume, profile, and supporting sources."
                ),
                action=(
                    f"Use {', '.join(matched[:4])} as the main keyword cluster."
                    if matched
                    else "Use the strongest verified skills as the main keyword cluster."
                ),
                priority="medium",
            ),
        ]
        summary = (
            f"Alternate view: the profile is at {readiness['overall']}/100, with the next gains "
            f"coming from clearer evidence for {specialization}."
        )
        explanation = (
            "This regenerated interpretation uses the same compact structured data, but frames the "
            "next steps as an evidence plan instead of repeating the default summary."
        )
    else:
        recommendations = [
            AIRecommendation(
                title="Strengthen the highest-impact gaps",
                rationale=(
                    "The current profile has measurable readiness signals, but the target role "
                    "still has unmatched requirements."
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
        summary = (
            f"The profile is currently scoring {readiness['overall']}/100 for "
            f"{specialization} readiness."
        )
        explanation = (
            "Snipe is combining deterministic resume quality, ATS readiness, profile completeness, "
            "and job-specific skill alignment signals. This interpretation uses compact structured "
            "profile data only."
        )
    return AIInterpretationResult(
        provider="local_template",
        model_name="local-template-v1",
        summary=summary,
        readiness_explanation=explanation,
        recommendations=recommendations,
        cautions=[
            (
                "Do not add skills, metrics, or achievements unless they are supported by "
                "real evidence."
            )
        ],
    )


def _local_template_resume_rewrite(context: dict[str, Any]) -> ResumeRewriteResult:
    bullets = context.get("existing_bullets") or []
    verified_skills = context.get("verified_skills") or []
    skill_gap = context.get("skill_gap") or {}
    generation_mode = context.get("generation_mode")
    matched = set(skill_gap.get("matched") or [])
    target_job = context.get("target_job") or {}
    target_keywords = []
    if isinstance(target_job, dict):
        target_keywords = [
            item
            for item in (
                target_job.get("required_skills", [])
                + target_job.get("preferred_skills", [])
                + target_job.get("ats_keywords", [])
            )
            if isinstance(item, str)
        ]
    suggestions: list[ResumeRewriteSuggestion] = []
    for bullet in bullets[:3]:
        evidence = _rewrite_evidence(
            verified_skills=verified_skills,
            matched=matched,
            target_keywords=target_keywords,
        )
        suggested, needs_candidate_value = _rewrite_bullet(
            bullet,
            evidence,
            alternate=generation_mode == "alternate",
        )
        suggestions.append(
            ResumeRewriteSuggestion(
                original=bullet,
                suggested=suggested,
                rationale=(
                    "This keeps the original claim and adds only verified evidence or a "
                    "candidate-supplied placeholder."
                ),
                evidence_used=evidence[:3],
                needs_candidate_value=needs_candidate_value,
            )
        )
    if not suggestions and verified_skills:
        suggestions.append(
            ResumeRewriteSuggestion(
                original="No rewriteable experience bullet was found.",
                suggested=(
                    "Add a real experience bullet that demonstrates "
                    f"{', '.join(verified_skills[:3])}."
                ),
                rationale="Snipe needs an existing fact before it can safely rewrite a bullet.",
                evidence_used=verified_skills[:3],
                needs_candidate_value=True,
            )
        )
    return ResumeRewriteResult(
        provider="local_template",
        model_name="local-template-v1",
        summary="Rewrite suggestions are based only on compact extracted resume evidence.",
        suggestions=suggestions,
        cautions=[
            (
                "Review every suggestion before use and replace placeholders only with true, "
                "verifiable details."
            )
        ],
    )


def _rewrite_evidence(
    *,
    verified_skills: list[str],
    matched: set[str],
    target_keywords: list[str],
) -> list[str]:
    verified = {skill.lower() for skill in verified_skills}
    normalized_targets = {keyword.lower() for keyword in target_keywords}
    matched_verified = sorted(verified & {skill.lower() for skill in matched})
    target_verified = sorted(verified & normalized_targets)
    return matched_verified[:3] or target_verified[:3] or verified_skills[:3]


def _rewrite_bullet(
    bullet: str,
    evidence: list[str],
    *,
    alternate: bool = False,
) -> tuple[str, bool]:
    cleaned = bullet.strip().rstrip(".")
    if evidence:
        evidence_text = ", ".join(evidence[:3])
        if alternate:
            suggested = (
                f"Applied {evidence_text} to support this work: {cleaned[0].lower()}"
                f"{cleaned[1:]}."
            )
        else:
            suggested = f"{cleaned}; emphasized verified strengths in {evidence_text}."
        if suggested.lower() != bullet.strip().lower():
            return suggested, False
    return (
        f"{cleaned}; add a true outcome or scope detail such as [candidate-supplied result].",
        True,
    )
