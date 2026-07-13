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


class KeywordInsertionRecommendation(BaseModel):
    keyword: str
    placement: str
    reason: str
    evidence_status: str = Field(pattern="^(verified|missing_evidence)$")


class ResumeTailoringPackageResult(BaseModel):
    output_type: str = "ai_resume_tailoring_package"
    output_version: str = "ai-resume-tailoring-package-v1"
    provider: str
    model_name: str
    summary: str
    tailored_summary: str
    skill_order: list[str] = Field(default_factory=list, max_length=20)
    keyword_recommendations: list[KeywordInsertionRecommendation] = Field(
        default_factory=list,
        max_length=12,
    )
    missing_evidence_warnings: list[str] = Field(default_factory=list, max_length=8)
    cautions: list[str] = Field(default_factory=list, max_length=5)
    cached: bool = False


class InterviewQuestion(BaseModel):
    category: str = Field(pattern="^(role_specific|technical|behavioral|screening)$")
    question: str
    why_it_matters: str
    answer_guidance: str
    evidence_to_use: list[str] = Field(default_factory=list, max_length=6)
    missing_evidence_warning: str | None = None


class InterviewPrepResult(BaseModel):
    output_type: str = "ai_interview_prep"
    output_version: str = "ai-interview-prep-v1"
    provider: str
    model_name: str
    summary: str
    questions: list[InterviewQuestion] = Field(default_factory=list, max_length=10)
    star_guidance: list[str] = Field(default_factory=list, max_length=6)
    missing_evidence_warnings: list[str] = Field(default_factory=list, max_length=8)
    cautions: list[str] = Field(default_factory=list, max_length=5)
    cached: bool = False


class ProjectRecommendation(BaseModel):
    title: str
    objective: str
    skills_practiced: list[str] = Field(default_factory=list, max_length=8)
    deliverables: list[str] = Field(default_factory=list, max_length=6)
    evidence_to_add: list[str] = Field(default_factory=list, max_length=6)
    missing_evidence_warning: str | None = None


class RoadmapStep(BaseModel):
    timeframe: str = Field(pattern="^(7_day|30_day|90_day)$")
    focus: str
    actions: list[str] = Field(default_factory=list, max_length=8)
    success_criteria: list[str] = Field(default_factory=list, max_length=6)


class ProjectRoadmapResult(BaseModel):
    output_type: str = "ai_project_roadmap_recommendations"
    output_version: str = "ai-project-roadmap-v1"
    provider: str
    model_name: str
    summary: str
    projects: list[ProjectRecommendation] = Field(default_factory=list, max_length=3)
    roadmap: list[RoadmapStep] = Field(default_factory=list, max_length=3)
    missing_evidence_warnings: list[str] = Field(default_factory=list, max_length=8)
    cautions: list[str] = Field(default_factory=list, max_length=5)
    cached: bool = False


class ApplicationMaterialsResult(BaseModel):
    output_type: str = "ai_application_materials"
    output_version: str = "ai-application-materials-v1"
    provider: str
    model_name: str
    summary: str
    cover_letter: str
    concise_cover_note: str
    email_application: str
    evidence_used: list[str] = Field(default_factory=list, max_length=8)
    missing_evidence_warnings: list[str] = Field(default_factory=list, max_length=8)
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

    def generate_resume_tailoring_package(
        self,
        context: dict[str, Any],
    ) -> ResumeTailoringPackageResult:
        if self.provider == "local_template":
            return _local_template_resume_tailoring(context)
        if self.provider in {"openai_compatible", "openai"}:
            return self._openai_compatible_resume_tailoring(context)
        raise AIProviderError(f"Unsupported AI_PROVIDER: {self.provider}.")

    def generate_interview_prep(self, context: dict[str, Any]) -> InterviewPrepResult:
        if self.provider == "local_template":
            return _local_template_interview_prep(context)
        if self.provider in {"openai_compatible", "openai"}:
            return self._openai_compatible_interview_prep(context)
        raise AIProviderError(f"Unsupported AI_PROVIDER: {self.provider}.")

    def generate_project_roadmap(self, context: dict[str, Any]) -> ProjectRoadmapResult:
        if self.provider == "local_template":
            return _local_template_project_roadmap(context)
        if self.provider in {"openai_compatible", "openai"}:
            return self._openai_compatible_project_roadmap(context)
        raise AIProviderError(f"Unsupported AI_PROVIDER: {self.provider}.")

    def generate_application_materials(
        self,
        context: dict[str, Any],
    ) -> ApplicationMaterialsResult:
        if self.provider == "local_template":
            return _local_template_application_materials(context)
        if self.provider in {"openai_compatible", "openai"}:
            return self._openai_compatible_application_materials(context)
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

    def _openai_compatible_resume_tailoring(
        self,
        context: dict[str, Any],
    ) -> ResumeTailoringPackageResult:
        parsed = self._openai_compatible_json(
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

    def _openai_compatible_interview_prep(
        self,
        context: dict[str, Any],
    ) -> InterviewPrepResult:
        parsed = self._openai_compatible_json(
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

    def _openai_compatible_project_roadmap(
        self,
        context: dict[str, Any],
    ) -> ProjectRoadmapResult:
        parsed = self._openai_compatible_json(
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

    def _openai_compatible_application_materials(
        self,
        context: dict[str, Any],
    ) -> ApplicationMaterialsResult:
        parsed = self._openai_compatible_json(
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
    verified_skills = context.get("skills") or []
    missing = skill_gap.get("missing") or []
    matched = skill_gap.get("matched") or []
    specialization = readiness.get("primary_specialization") or "the target career area"
    if not verified_skills:
        recommendations = [
            AIRecommendation(
                title="Add verified skills to the resume",
                rationale=(
                    "Snipe did not find clear skill evidence in the resume/profile. Skills such "
                    "as Excel, SQL, tools, methods, or profession-specific capabilities are major "
                    "resume and matching signals when they are true and supported."
                ),
                action=(
                    "Add a skills section and connect each important skill to real experience, "
                    "projects, coursework, certifications, or portfolio evidence."
                ),
                priority="high",
            ),
            AIRecommendation(
                title="Support each skill with proof",
                rationale=(
                    "A list of skills is weaker when the experience section does not show where "
                    "those skills were used."
                ),
                action=(
                    "For each skill you add, include one honest bullet or source that shows how "
                    "you used it. Do not add skills you cannot support."
                ),
                priority="high",
            ),
        ]
        summary = (
            "Snipe did not find verified skills or strong skill evidence in this profile yet."
        )
        explanation = (
            "Skills and supporting evidence are one of the main factors in resume quality, ATS "
            "matching, and job-fit analysis. Add only real skills that are supported by your "
            "experience, projects, education, certifications, portfolio, or LinkedIn content."
        )
    elif generation_mode == "alternate":
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
                    (
                        "Draft a new verified bullet around "
                        f"{', '.join(verified_skills[:3])}, then add a real scope or result."
                    )
                    if generation_mode == "alternate"
                    else (
                        "Add a real experience bullet that demonstrates "
                        f"{', '.join(verified_skills[:3])}."
                    )
                ),
                rationale="Snipe needs an existing fact before it can safely rewrite a bullet.",
                evidence_used=verified_skills[:3],
                needs_candidate_value=True,
            )
        )
    return ResumeRewriteResult(
        provider="local_template",
        model_name="local-template-v1",
        summary=(
            (
                "Regenerated view: no verified skills were found; add real, supported skills "
                "before relying on rewrites."
            )
            if not verified_skills and generation_mode == "alternate"
            else (
                "No verified skills were found; add real, supported skills before relying "
                "on rewrites."
            )
            if not verified_skills
            else
            "Regenerated rewrite suggestions use an alternate evidence-bound structure."
            if generation_mode == "alternate"
            else "Rewrite suggestions are based only on compact extracted resume evidence."
        ),
        suggestions=suggestions,
        cautions=[
            (
                "Snipe did not find verified skills such as Excel, SQL, tools, methods, or "
                "profession-specific capabilities. Add only real skills you can support."
            )
            if not verified_skills
            else (
                "Review every suggestion before use and replace placeholders only with true, "
                "verifiable details."
            )
        ],
    )


def _local_template_resume_tailoring(context: dict[str, Any]) -> ResumeTailoringPackageResult:
    verified_skills = context.get("verified_skills") or []
    target_job = context.get("target_job") or {}
    skill_gap = context.get("skill_gap") or {}
    generation_mode = context.get("generation_mode")
    required = _string_list(
        target_job.get("required_skills") if isinstance(target_job, dict) else []
    )
    preferred = _string_list(
        target_job.get("preferred_skills") if isinstance(target_job, dict) else []
    )
    ats_keywords = _string_list(
        target_job.get("ats_keywords") if isinstance(target_job, dict) else []
    )
    matched = _string_list(skill_gap.get("matched") if isinstance(skill_gap, dict) else [])
    missing = _string_list(skill_gap.get("missing") if isinstance(skill_gap, dict) else [])
    verified_lookup = {skill.lower(): skill for skill in verified_skills}
    ordered_skills = _ordered_tailored_skills(
        verified_skills=verified_skills,
        required=required,
        preferred=preferred,
        ats_keywords=ats_keywords,
        matched=matched,
        alternate=generation_mode == "alternate",
    )
    keyword_recommendations = _keyword_recommendations(
        ordered_skills=ordered_skills,
        missing=missing,
        required=required,
        verified_lookup=verified_lookup,
    )
    missing_warnings = [
        (
            f"{keyword} appears important for the target role, but Snipe did not find "
            "supporting evidence. Add it only if it is true and backed by experience, "
            "projects, education, certification, portfolio, or LinkedIn evidence."
        )
        for keyword in missing[:6]
    ]
    if not verified_skills:
        missing_warnings.insert(
            0,
            (
                "No verified skills were found in the profile. Add a real skills section before "
                "tailoring keywords."
            ),
        )
    role = target_job.get("title") if isinstance(target_job, dict) else None
    tailored_summary = _tailored_summary(
        role=role,
        ordered_skills=ordered_skills,
        alternate=generation_mode == "alternate",
    )
    return ResumeTailoringPackageResult(
        provider="local_template",
        model_name="local-template-v1",
        summary=(
            "Regenerated tailoring package uses an alternate evidence-bound structure."
            if verified_skills and generation_mode == "alternate"
            else (
                "Regenerated tailoring is limited because no verified skills were found."
            )
            if generation_mode == "alternate"
            else
            "Tailoring package generated from verified skills and target-job requirements."
            if verified_skills
            else "Tailoring is limited because no verified skills were found."
        ),
        tailored_summary=tailored_summary,
        skill_order=ordered_skills,
        keyword_recommendations=keyword_recommendations,
        missing_evidence_warnings=missing_warnings,
        cautions=[
            (
                "Do not add keywords, tools, achievements, or metrics unless they are true and "
                "supported by real evidence."
            )
        ],
    )


def _local_template_interview_prep(context: dict[str, Any]) -> InterviewPrepResult:
    verified_skills = _string_list(context.get("verified_skills"))
    experience_signals = _string_list(context.get("experience_signals"))
    target_job = context.get("target_job") or {}
    skill_gap = context.get("skill_gap") or {}
    readiness = context.get("readiness") or {}
    generation_mode = context.get("generation_mode")
    role = target_job.get("title") if isinstance(target_job, dict) else None
    role_name = role or readiness.get("primary_specialization") or "the target role"
    required = _string_list(
        target_job.get("required_skills") if isinstance(target_job, dict) else []
    )
    preferred = _string_list(
        target_job.get("preferred_skills") if isinstance(target_job, dict) else []
    )
    missing = _string_list(skill_gap.get("missing") if isinstance(skill_gap, dict) else [])
    matched = _string_list(skill_gap.get("matched") if isinstance(skill_gap, dict) else [])
    priority_skills = _interview_priority_skills(
        verified_skills=verified_skills,
        matched=matched,
        required=required,
        preferred=preferred,
        alternate=generation_mode == "alternate",
    )
    questions: list[InterviewQuestion] = [
        InterviewQuestion(
            category="role_specific",
            question=(
                f"What parts of the {role_name} role are you strongest in, and where would "
                "you need onboarding?"
                if generation_mode == "alternate"
                else f"How would you approach the main responsibilities of a {role_name}?"
            ),
            why_it_matters=(
                "This checks whether the candidate understands the role and can map real "
                "evidence to it."
            ),
            answer_guidance=(
                "Use verified strengths first, then name any gaps honestly and explain the "
                "learning plan without claiming unsupported experience."
            ),
            evidence_to_use=(priority_skills[:3] or experience_signals[:2]),
            missing_evidence_warning=(
                None
                if priority_skills or experience_signals
                else (
                    "No verified role evidence was found; add real skills or experience before "
                    "using a strong answer."
                )
            ),
        )
    ]
    for skill in priority_skills[:3]:
        questions.append(
            InterviewQuestion(
                category="technical",
                question=(
                    f"Walk me through a practical example where {skill} affected your work."
                    if generation_mode == "alternate"
                    else f"Tell me about a time you used {skill} in real work or a project."
                ),
                why_it_matters=(
                    "This verifies that a listed skill is supported by practical evidence."
                ),
                answer_guidance=(
                    "Give a real situation, the task you owned, the actions you took, and the "
                    "result. Add a metric only if it is true."
                ),
                evidence_to_use=[skill],
            )
        )
    if experience_signals:
        signal = experience_signals[0]
        questions.append(
            InterviewQuestion(
                category="behavioral",
                question=(
                    "Describe a challenge from one of your listed experiences and how you "
                    "handled it."
                    if generation_mode == "alternate"
                    else f"Tell me about a challenge related to this experience: {signal}"
                ),
                why_it_matters=(
                    "Behavioral questions test decision-making, ownership, and communication."
                ),
                answer_guidance=(
                    "Use the STAR structure and keep the example tied to the actual experience "
                    "signal Snipe found."
                ),
                evidence_to_use=[signal],
            )
        )
    for skill in missing[:3]:
        questions.append(
            InterviewQuestion(
                category="screening",
                question=f"If asked about {skill}, how should you answer honestly?",
                why_it_matters=(
                    "The target job mentions this area, but the profile does not verify it."
                ),
                answer_guidance=(
                    "Do not claim experience you do not have. State your actual exposure, related "
                    "transferable experience, or a concrete learning plan."
                ),
                evidence_to_use=[],
                missing_evidence_warning=(
                    f"{skill} is not supported by verified profile evidence. Add it only after "
                    "real experience, education, certification, portfolio, or LinkedIn "
                    "evidence exists."
                ),
            )
        )
    warnings = [
        (
            f"{skill} appears important for the target role, but Snipe did not find verified "
            "evidence for it."
        )
        for skill in missing[:6]
    ]
    if not verified_skills:
        warnings.insert(
            0,
            (
                "No verified skills were found. Add real evidence for skills such as Excel, "
                "SQL, tools, methods, or profession-specific capabilities before practicing "
                "strong skill-based answers."
            ),
        )
    return InterviewPrepResult(
        provider="local_template",
        model_name="local-template-v1",
        summary=(
            "Regenerated interview prep uses an alternate evidence-bound question set."
            if verified_skills and generation_mode == "alternate"
            else (
                "Regenerated interview prep is limited because no verified skills were found."
            )
            if generation_mode == "alternate"
            else (
                "Interview prep generated from verified profile signals and target-job "
                "requirements."
            )
            if verified_skills
            else "Interview prep is limited because no verified skills were found."
        ),
        questions=questions[:10],
        star_guidance=[
            "Situation: choose a real work, project, education, or portfolio context.",
            "Task: state your actual responsibility without expanding your role.",
            "Action: describe specific steps you personally took.",
            "Result: include a true outcome; use a bracketed placeholder only until you verify it.",
            "Do not include unsupported skills, metrics, employers, credentials, or achievements.",
        ],
        missing_evidence_warnings=warnings[:8],
        cautions=[
            (
                "Practice answers should be based on real evidence. Do not memorize fabricated "
                "stories or unsupported claims."
            )
        ],
    )


def _local_template_project_roadmap(context: dict[str, Any]) -> ProjectRoadmapResult:
    verified_skills = _string_list(context.get("verified_skills"))
    target_job = context.get("target_job") or {}
    skill_gap = context.get("skill_gap") or {}
    readiness = context.get("readiness") or {}
    generation_mode = context.get("generation_mode")
    role = target_job.get("title") if isinstance(target_job, dict) else None
    role_name = role or readiness.get("primary_specialization") or "the target role"
    required = _string_list(
        target_job.get("required_skills") if isinstance(target_job, dict) else []
    )
    preferred = _string_list(
        target_job.get("preferred_skills") if isinstance(target_job, dict) else []
    )
    matched = _string_list(skill_gap.get("matched") if isinstance(skill_gap, dict) else [])
    missing = _string_list(skill_gap.get("missing") if isinstance(skill_gap, dict) else [])
    priority_skills = _interview_priority_skills(
        verified_skills=verified_skills,
        matched=matched,
        required=required,
        preferred=preferred,
        alternate=generation_mode == "alternate",
    )
    practice_targets = missing[:3] or required[:3] or preferred[:3]
    if generation_mode == "alternate":
        project_templates = [
            ("Evidence Portfolio Sprint", "Create visible proof around target-role requirements."),
            (
                "Workflow Improvement Case Study",
                "Show structured problem solving with real context.",
            ),
            ("Role Simulation Pack", "Practice realistic tasks for interview and resume evidence."),
        ]
    else:
        project_templates = [
            ("Target Role Case Study", "Build a focused artifact for the target role."),
            ("Skills Evidence Project", "Create proof for verified and missing skill areas."),
            ("Portfolio Readiness Sprint", "Package credible examples for applications."),
        ]
    project_skills = priority_skills[:4] or practice_targets[:4]
    projects = [
        ProjectRecommendation(
            title=title,
            objective=(
                f"{objective} Align it with {role_name} without claiming it is completed."
            ),
            skills_practiced=project_skills,
            deliverables=[
                "one-page project brief",
                "work sample or documented artifact",
                "short reflection with true scope and outcome",
            ],
            evidence_to_add=[
                "project link or file",
                "skills used",
                "candidate-verified outcome or lesson",
            ],
            missing_evidence_warning=(
                None
                if project_skills
                else (
                    "No verified skills were found; define real skills before positioning a "
                    "project."
                )
            ),
        )
        for title, objective in project_templates
    ]
    roadmap = [
        RoadmapStep(
            timeframe="7_day",
            focus="Select one realistic project and define evidence requirements.",
            actions=[
                f"Choose a project tied to {role_name}.",
                "List verified skills that can honestly be used.",
                (
                    f"Pick one missing skill to learn or evidence honestly: {practice_targets[0]}."
                    if practice_targets
                    else "Add a real skills section before selecting target keywords."
                ),
            ],
            success_criteria=[
                "project scope is documented",
                "unsupported claims are removed",
                "next evidence artifact is identified",
            ],
        ),
        RoadmapStep(
            timeframe="30_day",
            focus="Build and document the first evidence artifact.",
            actions=[
                "Complete a small work sample or case study.",
                "Record what was actually done, learned, and produced.",
                "Map the artifact to resume bullets only where evidence exists.",
            ],
            success_criteria=[
                "artifact is reviewable",
                "skills are tied to real proof",
                "resume or portfolio update is drafted",
            ],
        ),
        RoadmapStep(
            timeframe="90_day",
            focus="Expand proof and prepare application-ready materials.",
            actions=[
                "Create one additional artifact for a target gap.",
                "Update resume, portfolio, and interview examples with true evidence.",
                "Review gaps against the target job and adjust the next project.",
            ],
            success_criteria=[
                "two evidence artifacts exist",
                "interview examples are evidence-bound",
                "remaining gaps have a learning plan",
            ],
        ),
    ]
    warnings = [
        (
            f"{skill} is a target gap. Recommend practicing it, but do not list it as a skill "
            "until real evidence exists."
        )
        for skill in missing[:6]
    ]
    if not verified_skills:
        warnings.insert(
            0,
            (
                "No verified skills were found. Add real skills and evidence before treating "
                "project recommendations as application proof."
            ),
        )
    return ProjectRoadmapResult(
        provider="local_template",
        model_name="local-template-v1",
        summary=(
            "Regenerated project roadmap uses an alternate evidence-building sequence."
            if verified_skills and generation_mode == "alternate"
            else (
                "Regenerated project roadmap is limited because no verified skills were found."
            )
            if generation_mode == "alternate"
            else "Project roadmap generated from verified skills and target-role gaps."
            if verified_skills
            else "Project roadmap is limited because no verified skills were found."
        ),
        projects=projects,
        roadmap=roadmap,
        missing_evidence_warnings=warnings[:8],
        cautions=[
            (
                "Treat these as future work recommendations. Do not present a project, skill, "
                "metric, or outcome as completed until it is true and supported by evidence."
            )
        ],
    )


def _local_template_application_materials(
    context: dict[str, Any],
) -> ApplicationMaterialsResult:
    verified_skills = _string_list(context.get("verified_skills"))
    experience_signals = _string_list(context.get("experience_signals"))
    target_job = context.get("target_job") or {}
    skill_gap = context.get("skill_gap") or {}
    readiness = context.get("readiness") or {}
    generation_mode = context.get("generation_mode")
    role = target_job.get("title") if isinstance(target_job, dict) else None
    company = target_job.get("company") if isinstance(target_job, dict) else None
    role_name = role or readiness.get("primary_specialization") or "the target role"
    company_name = company or "[company name]"
    matched = _string_list(skill_gap.get("matched") if isinstance(skill_gap, dict) else [])
    missing = _string_list(skill_gap.get("missing") if isinstance(skill_gap, dict) else [])
    required = _string_list(
        target_job.get("required_skills") if isinstance(target_job, dict) else []
    )
    evidence = _application_evidence(
        verified_skills=verified_skills,
        matched=matched,
        required=required,
        experience_signals=experience_signals,
        alternate=generation_mode == "alternate",
    )
    skill_text = ", ".join(evidence[:4]) if evidence else "[candidate-verified skills]"
    experience_text = (
        experience_signals[0]
        if experience_signals
        else "[candidate-verified experience example]"
    )
    cover_letter = (
        f"Dear {company_name} hiring team,\n\n"
        f"I am interested in the {role_name} opportunity. My strongest verified signals for "
        f"this role are {skill_text}. In my background, I can point to: {experience_text}. "
        "I would use the interview process to discuss the real scope, tools, and outcomes I "
        "can verify.\n\n"
        "I am especially interested in this role because it aligns with the requirements in "
        "the job description and gives me a practical path to contribute with evidence-backed "
        "strengths. Where the role requires skills not yet shown in my profile, I would be "
        "transparent and discuss my learning plan rather than overstate experience.\n\n"
        "Thank you for your consideration,\n[candidate name]"
    )
    if generation_mode == "alternate":
        cover_letter = (
            f"Dear {company_name} hiring team,\n\n"
            f"I am applying for the {role_name} role with verified strengths in {skill_text}. "
            f"A relevant evidence signal from my profile is: {experience_text}. I have kept "
            "this draft limited to details that should be reviewed and confirmed before use.\n\n"
            "The role appears to value practical execution and clear evidence. I would welcome "
            "the chance to connect my verified background to your needs and address any gaps "
            "honestly.\n\n"
            "Sincerely,\n[candidate name]"
        )
    concise_note = (
        f"I am interested in the {role_name} role at {company_name}. My verified profile "
        f"signals include {skill_text}. I can share evidence around {experience_text} and "
        "will only add additional claims after confirming they are accurate."
    )
    email_application = (
        f"Subject: Application for {role_name}\n\n"
        f"Hello {company_name} hiring team,\n\n"
        f"I am submitting my application for the {role_name} role. My profile shows verified "
        f"signals in {skill_text}, with supporting experience such as: {experience_text}.\n\n"
        "I have attached my resume for review. Please let me know if additional information "
        "would be helpful.\n\n"
        "Best,\n[candidate name]"
    )
    warnings = [
        (
            f"{skill} appears important for the target role, but Snipe did not find verified "
            "evidence. Do not claim it in application materials until it is true and supported."
        )
        for skill in missing[:6]
    ]
    if not verified_skills:
        warnings.insert(
            0,
            (
                "No verified skills were found. Add real skills and evidence before using "
                "strong application-material claims."
            ),
        )
    return ApplicationMaterialsResult(
        provider="local_template",
        model_name="local-template-v1",
        summary=(
            "Regenerated application materials use alternate evidence-bound wording."
            if verified_skills and generation_mode == "alternate"
            else (
                "Regenerated application materials are limited because no verified skills were "
                "found."
            )
            if generation_mode == "alternate"
            else "Application materials generated from verified profile and target-role signals."
            if verified_skills
            else "Application materials are limited because no verified skills were found."
        ),
        cover_letter=cover_letter,
        concise_cover_note=concise_note,
        email_application=email_application,
        evidence_used=evidence[:8],
        missing_evidence_warnings=warnings[:8],
        cautions=[
            (
                "Review before sending. Replace placeholders only with true details and do not "
                "add unsupported skills, metrics, achievements, employers, or credentials."
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


def _ordered_tailored_skills(
    *,
    verified_skills: list[str],
    required: list[str],
    preferred: list[str],
    ats_keywords: list[str],
    matched: list[str],
    alternate: bool = False,
) -> list[str]:
    verified_lookup = {skill.lower(): skill for skill in verified_skills}
    priority_terms = (
        matched + ats_keywords + required + preferred
        if alternate
        else required + preferred + ats_keywords + matched
    )
    ordered: list[str] = []
    for term in priority_terms:
        key = term.lower()
        if key in verified_lookup and verified_lookup[key] not in ordered:
            ordered.append(verified_lookup[key])
    for skill in verified_skills:
        if skill not in ordered:
            ordered.append(skill)
    return ordered[:20]


def _interview_priority_skills(
    *,
    verified_skills: list[str],
    matched: list[str],
    required: list[str],
    preferred: list[str],
    alternate: bool = False,
) -> list[str]:
    verified_lookup = {skill.lower(): skill for skill in verified_skills}
    priority_terms = (
        matched + preferred + required if alternate else required + matched + preferred
    )
    ordered: list[str] = []
    for term in priority_terms:
        key = term.lower()
        if key in verified_lookup and verified_lookup[key] not in ordered:
            ordered.append(verified_lookup[key])
    for skill in verified_skills:
        if skill not in ordered:
            ordered.append(skill)
    return ordered[:8]


def _application_evidence(
    *,
    verified_skills: list[str],
    matched: list[str],
    required: list[str],
    experience_signals: list[str],
    alternate: bool = False,
) -> list[str]:
    verified_lookup = {skill.lower(): skill for skill in verified_skills}
    priority_terms = matched + required if alternate else required + matched
    ordered: list[str] = []
    for term in priority_terms:
        key = term.lower()
        if key in verified_lookup and verified_lookup[key] not in ordered:
            ordered.append(verified_lookup[key])
    for skill in verified_skills:
        if skill not in ordered:
            ordered.append(skill)
    ordered.extend(signal for signal in experience_signals[:2] if signal not in ordered)
    return ordered[:8]


def _keyword_recommendations(
    *,
    ordered_skills: list[str],
    missing: list[str],
    required: list[str],
    verified_lookup: dict[str, str],
) -> list[KeywordInsertionRecommendation]:
    recommendations: list[KeywordInsertionRecommendation] = []
    for skill in ordered_skills[:8]:
        recommendations.append(
            KeywordInsertionRecommendation(
                keyword=skill,
                placement="skills section and one relevant experience bullet",
                reason="This skill is verified and should be easy for ATS/recruiters to scan.",
                evidence_status="verified",
            )
        )
    for keyword in missing[:4]:
        if keyword.lower() not in verified_lookup:
            recommendations.append(
                KeywordInsertionRecommendation(
                    keyword=keyword,
                    placement="do not add until supporting evidence exists",
                    reason=(
                        "This target keyword is not currently supported by verified profile data."
                    ),
                    evidence_status="missing_evidence",
                )
            )
    if not recommendations and required:
        for keyword in required[:4]:
            recommendations.append(
                KeywordInsertionRecommendation(
                    keyword=keyword,
                    placement="add only after real supporting evidence is available",
                    reason="This requirement appears in the target job but is not verified.",
                    evidence_status="missing_evidence",
                )
            )
    return recommendations[:12]


def _tailored_summary(
    role: str | None,
    ordered_skills: list[str],
    *,
    alternate: bool = False,
) -> str:
    if ordered_skills:
        skill_text = ", ".join(ordered_skills[:4])
        if role:
            if alternate:
                return (
                    f"For {role} applications, lead with verified strengths in {skill_text}; "
                    "keep unsupported keywords out until real evidence is available."
                )
            return (
                f"Candidate targeting {role} roles with verified experience signals in "
                f"{skill_text}. Add only true outcomes and scope details where supported."
            )
        if alternate:
            return (
                f"Lead with verified strengths in {skill_text}, then add only evidence-backed "
                "scope or outcome details."
            )
        return (
            f"Candidate with verified experience signals in {skill_text}. Add only true "
            "outcomes and scope details where supported."
        )
    if role:
        return (
            f"Candidate targeting {role} roles. Add real, supported skills and evidence before "
            "using a tailored summary."
        )
    return "Add real, supported skills and evidence before using a tailored summary."


def _string_list(value: Any) -> list[str]:
    return [item for item in value if isinstance(item, str)] if isinstance(value, list) else []


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
        (
            "Reframe this bullet with a real scope/result supplied by the candidate: "
            f"{cleaned}; [candidate-supplied scope or result]."
            if alternate
            else (
                f"{cleaned}; add a true outcome or scope detail such as "
                "[candidate-supplied result]."
            )
        ),
        True,
    )
