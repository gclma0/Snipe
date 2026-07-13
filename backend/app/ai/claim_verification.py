import json
from hashlib import sha256
from typing import Any

from pydantic import BaseModel, Field

CLAIM_VERIFICATION_VERSION = "ai-claim-verification-v1"
CLAIM_VERIFICATION_CONTEXT_VERSION = "ai-claim-verification-context-v1"


class ClaimQuestion(BaseModel):
    claim: str
    evidence_strength: str = Field(pattern="^(strong|moderate|needs_clarification|missing)$")
    question: str
    why_it_matters: str
    evidence_to_prepare: list[str] = Field(default_factory=list, max_length=5)
    caution: str | None = None


class ClaimVerificationResult(BaseModel):
    output_type: str = "ai_claim_verification_questions"
    output_version: str = CLAIM_VERIFICATION_VERSION
    provider: str = "deterministic"
    model_name: str = "deterministic-claim-verification-v1"
    summary: str
    questions: list[ClaimQuestion] = Field(default_factory=list, max_length=10)
    evidence_strength_notes: list[str] = Field(default_factory=list, max_length=8)
    cautions: list[str] = Field(default_factory=list, max_length=5)
    cached: bool = False


def build_claim_verification_context(
    *,
    normalized_profile: dict[str, Any],
    structured_job: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "context_version": CLAIM_VERIFICATION_CONTEXT_VERSION,
        "claims": _profile_claims(normalized_profile),
        "target_job": _job_summary(structured_job),
        "constraints": [
            "Use evidence strength and clarification language.",
            "Do not describe the system as a lie detector.",
            "Do not fabricate achievements, metrics, skills, or experience.",
        ],
    }


def claim_verification_context_hash(context: dict[str, Any]) -> str:
    encoded = json.dumps(context, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def generate_claim_verification_questions(context: dict[str, Any]) -> ClaimVerificationResult:
    claims = context.get("claims") if isinstance(context.get("claims"), list) else []
    target_job = context.get("target_job") if isinstance(context.get("target_job"), dict) else {}
    required_skills = _string_list(target_job.get("required_skills") if target_job else [])
    questions = [_question_for_claim(claim, required_skills) for claim in claims[:8]]
    missing_required = [
        skill
        for skill in required_skills
        if skill not in {str(claim.get("normalized_value", "")).lower() for claim in claims}
    ][:3]
    for skill in missing_required:
        questions.append(
            ClaimQuestion(
                claim=f"Target role requirement: {skill}",
                evidence_strength="missing",
                question=(
                    f"If asked about {skill}, what truthful related experience or learning "
                    "plan can you explain?"
                ),
                why_it_matters=(
                    "The target role mentions this requirement, but the profile does not "
                    "verify it."
                ),
                evidence_to_prepare=[],
                caution=f"Do not present {skill} as a verified skill until real evidence exists.",
            )
        )

    notes = [
        "Evidence strength: strong means the profile includes a specific skill or "
        "experience excerpt.",
        "Evidence strength: moderate means the profile mentions the area but lacks "
        "concrete detail.",
        "Evidence strength: needs clarification means an interviewer may ask for scope, "
        "ownership, tools, or outcomes.",
        "Evidence strength: missing means the candidate should not claim the skill or "
        "experience as verified.",
    ]
    if not questions:
        notes.insert(0, "No profile claims were available for evidence-strength questions.")

    return ClaimVerificationResult(
        summary="Claim questions generated with evidence-strength notes.",
        questions=questions[:10],
        evidence_strength_notes=notes,
        cautions=[
            "Use these questions to prepare accurate examples and clarify evidence gaps.",
            "Do not add metrics, achievements, skills, or responsibilities unless they are true.",
        ],
    )


def _profile_claims(normalized_profile: dict[str, Any]) -> list[dict[str, str]]:
    claims: list[dict[str, str]] = []
    skills = normalized_profile.get("skills")
    if isinstance(skills, list):
        for skill in skills:
            if isinstance(skill, dict) and isinstance(skill.get("name"), str):
                claims.append(
                    {
                        "claim_type": "skill",
                        "normalized_value": skill["name"].strip().lower(),
                        "excerpt": str(skill.get("source") or "profile skill"),
                    }
                )
    sections = normalized_profile.get("sections")
    if isinstance(sections, dict):
        for key in ("experience", "projects", "summary"):
            value = sections.get(key)
            if isinstance(value, str) and value.strip():
                claims.append(
                    {
                        "claim_type": key,
                        "normalized_value": key,
                        "excerpt": value[:240],
                    }
                )
    return claims[:12]


def _question_for_claim(claim: dict[str, Any], required_skills: list[str]) -> ClaimQuestion:
    claim_type = str(claim.get("claim_type") or "profile")
    value = str(claim.get("normalized_value") or claim_type)
    excerpt = str(claim.get("excerpt") or "")
    evidence_strength = _evidence_strength(claim_type, value, excerpt, required_skills)
    return ClaimQuestion(
        claim=value,
        evidence_strength=evidence_strength,
        question=_question_text(claim_type, value),
        why_it_matters=(
            "Interviewers often ask for scope, ownership, tools, and outcomes behind resume claims."
        ),
        evidence_to_prepare=_evidence_to_prepare(claim_type, value, excerpt),
        caution=(
            "Prepare a concrete example before using this as a strong interview claim."
            if evidence_strength in {"moderate", "needs_clarification"}
            else None
        ),
    )


def _evidence_strength(
    claim_type: str,
    value: str,
    excerpt: str,
    required_skills: list[str],
) -> str:
    if claim_type == "skill" and value in required_skills and excerpt:
        return "strong"
    if claim_type == "skill" and excerpt:
        return "moderate"
    if claim_type in {"experience", "projects"} and len(excerpt.split()) >= 8:
        return "needs_clarification"
    return "missing"


def _question_text(claim_type: str, value: str) -> str:
    if claim_type == "skill":
        return f"What specific example proves your experience with {value}?"
    if claim_type == "projects":
        return (
            "What did you personally build or contribute in this project, and what "
            "evidence can you show?"
        )
    if claim_type == "experience":
        return (
            "What was your exact responsibility in this experience, and what outcome "
            "can you verify?"
        )
    return "Which real example best supports this profile statement?"


def _evidence_to_prepare(claim_type: str, value: str, excerpt: str) -> list[str]:
    evidence = []
    if excerpt:
        evidence.append(excerpt[:180])
    if claim_type == "skill":
        evidence.append(f"A real task, project, course, or work example involving {value}.")
    evidence.append("Accurate scope, tools used, personal contribution, and truthful outcome.")
    return evidence[:5]


def _job_summary(structured_job: dict[str, Any] | None) -> dict[str, Any] | None:
    if not structured_job:
        return None
    return {
        "title": structured_job.get("title"),
        "required_skills": _string_list(structured_job.get("required_skills")),
        "preferred_skills": _string_list(structured_job.get("preferred_skills")),
    }


def _string_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    return [value.strip().lower() for value in values if isinstance(value, str) and value.strip()]
