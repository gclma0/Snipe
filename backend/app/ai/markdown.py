from app.ai.career_transition import CareerTransitionResult
from app.ai.claim_verification import ClaimVerificationResult
from app.ai.outreach import OutreachMessagePack
from app.ai.schemas import (
    AIInterpretationResult,
    ApplicationMaterialsResult,
    InterviewPrepResult,
    LearningPlanResult,
    ProjectRoadmapResult,
    ResumeRewriteResult,
    ResumeTailoringPackageResult,
)


def interpretation_markdown(result: AIInterpretationResult) -> str:
    lines = ["# Snipe AI Interpretation", "", result.summary, "", result.readiness_explanation, ""]
    lines.append("## Recommendations")
    for item in result.recommendations:
        lines.extend(["", f"### {item.title}", item.rationale, item.action])
    if result.cautions:
        lines.extend(["", "## Cautions"])
        lines.extend(f"- {caution}" for caution in result.cautions)
    return "\n".join(lines)


def rewrite_markdown(result: ResumeRewriteResult) -> str:
    lines = ["# Snipe Resume Rewrite Suggestions", "", result.summary, ""]
    for item in result.suggestions:
        lines.extend(
            [
                "## Suggestion",
                f"Original: {item.original}",
                f"Suggested: {item.suggested}",
                f"Why: {item.rationale}",
                "",
            ]
        )
    if result.cautions:
        lines.append("## Cautions")
        lines.extend(f"- {caution}" for caution in result.cautions)
    return "\n".join(lines)


def tailoring_markdown(result: ResumeTailoringPackageResult) -> str:
    lines = ["# Snipe Resume Tailoring Package", "", result.summary, ""]
    lines.extend(["## Tailored Summary", result.tailored_summary, ""])
    if result.skill_order:
        lines.append("## Skill Order")
        lines.extend(f"- {skill}" for skill in result.skill_order)
        lines.append("")
    if result.keyword_recommendations:
        lines.append("## Keyword Recommendations")
        for item in result.keyword_recommendations:
            lines.extend(
                [
                    f"- {item.keyword}: {item.placement}",
                    f"  Reason: {item.reason}",
                ]
            )
        lines.append("")
    if result.missing_evidence_warnings:
        lines.append("## Missing Evidence Warnings")
        lines.extend(f"- {warning}" for warning in result.missing_evidence_warnings)
        lines.append("")
    if result.cautions:
        lines.append("## Cautions")
        lines.extend(f"- {caution}" for caution in result.cautions)
    return "\n".join(lines)


def interview_markdown(result: InterviewPrepResult) -> str:
    lines = ["# Snipe Interview Prep", "", result.summary, ""]
    if result.star_guidance:
        lines.append("## STAR Guidance")
        lines.extend(f"- {item}" for item in result.star_guidance)
        lines.append("")
    if result.questions:
        lines.append("## Practice Questions")
        for item in result.questions:
            lines.extend(
                [
                    f"### {item.category.replace('_', ' ').title()}",
                    item.question,
                    f"Why: {item.why_it_matters}",
                    f"Guidance: {item.answer_guidance}",
                    "",
                ]
            )
    if result.missing_evidence_warnings:
        lines.append("## Missing Evidence Warnings")
        lines.extend(f"- {warning}" for warning in result.missing_evidence_warnings)
        lines.append("")
    if result.cautions:
        lines.append("## Cautions")
        lines.extend(f"- {caution}" for caution in result.cautions)
    return "\n".join(lines)


def claim_verification_markdown(result: ClaimVerificationResult) -> str:
    lines = ["# Snipe Claim Questions", "", result.summary, ""]
    if result.questions:
        lines.append("## Questions")
        for item in result.questions:
            lines.extend(
                [
                    f"### {item.claim}",
                    f"Evidence strength: {item.evidence_strength.replace('_', ' ')}",
                    item.question,
                    f"Why: {item.why_it_matters}",
                    "",
                ]
            )
    if result.evidence_strength_notes:
        lines.append("## Evidence Strength Notes")
        lines.extend(f"- {note}" for note in result.evidence_strength_notes)
        lines.append("")
    if result.cautions:
        lines.append("## Cautions")
        lines.extend(f"- {caution}" for caution in result.cautions)
    return "\n".join(lines)


def outreach_markdown(result: OutreachMessagePack) -> str:
    lines = ["# Snipe Outreach Message Pack", "", result.summary, ""]
    sections = [
        ("LinkedIn Connection Message", result.linkedin_connection_message),
        ("Recruiter Outreach Message", result.recruiter_outreach_message),
        ("Job Application Email", result.job_application_email),
        ("Follow-Up Email", result.follow_up_email),
        ("Interview Thank-You Email", result.interview_thank_you_email),
        ("Referral Request", result.referral_request),
        ("Short Professional Intro", result.short_professional_intro),
    ]
    for title, content in sections:
        lines.extend([f"## {title}", content, ""])
    if result.evidence_used:
        lines.append("## Evidence Used")
        lines.extend(f"- {item}" for item in result.evidence_used)
        lines.append("")
    if result.missing_evidence_warnings:
        lines.append("## Missing Evidence")
        lines.extend(f"- {item}" for item in result.missing_evidence_warnings)
        lines.append("")
    if result.cautions:
        lines.append("## Cautions")
        lines.extend(f"- {item}" for item in result.cautions)
    return "\n".join(lines)


def career_transition_markdown(result: CareerTransitionResult) -> str:
    lines = ["# Snipe Career Transition Analysis", "", result.summary, ""]
    sections = [
        ("Transferable Skills", result.transferable_skills),
        ("Reframed Experience", result.reframed_experience),
        ("Missing Foundational Knowledge", result.missing_foundational_knowledge),
        ("Transitional Roles", result.transitional_roles),
        ("Recommended Projects", result.recommended_projects),
        ("Learning Sequence", result.learning_sequence),
        ("Resume Positioning", result.resume_positioning),
        ("Likely Interview Concerns", result.likely_interview_concerns),
        ("Cautions", result.cautions),
    ]
    for title, values in sections:
        if values:
            lines.append(f"## {title}")
            lines.extend(f"- {item}" for item in values)
            lines.append("")
    return "\n".join(lines).strip()


def project_roadmap_markdown(result: ProjectRoadmapResult) -> str:
    lines = ["# Snipe Project Roadmap", "", result.summary, ""]
    if result.projects:
        lines.append("## Project Recommendations")
        for item in result.projects:
            lines.extend(
                [
                    f"### {item.title}",
                    item.objective,
                    "",
                    "Skills practiced:",
                    *[f"- {skill}" for skill in item.skills_practiced],
                    "Deliverables:",
                    *[f"- {deliverable}" for deliverable in item.deliverables],
                    "",
                ]
            )
    if result.roadmap:
        lines.append("## Roadmap")
        for item in result.roadmap:
            lines.extend(
                [
                    f"### {item.timeframe.replace('_', ' ').title()}",
                    item.focus,
                    "",
                    "Actions:",
                    *[f"- {action}" for action in item.actions],
                    "Success criteria:",
                    *[f"- {criterion}" for criterion in item.success_criteria],
                    "",
                ]
            )
    if result.missing_evidence_warnings:
        lines.append("## Missing Evidence Warnings")
        lines.extend(f"- {warning}" for warning in result.missing_evidence_warnings)
        lines.append("")
    if result.cautions:
        lines.append("## Cautions")
        lines.extend(f"- {caution}" for caution in result.cautions)
    return "\n".join(lines)


def learning_plan_markdown(result: LearningPlanResult) -> str:
    lines = ["# Snipe Learning Plan", "", result.summary, ""]
    sections = [
        ("Daily Plan", result.daily_plan),
        ("Weekly Plan", result.weekly_plan),
        ("Monthly Plan", result.monthly_plan),
    ]
    for title, steps in sections:
        if not steps:
            continue
        lines.append(f"## {title}")
        for item in steps:
            lines.extend(
                [
                    f"### {item.title}",
                    "Tasks:",
                    *[f"- {task}" for task in item.tasks],
                    f"Practice: {item.practice_activity}",
                    f"Evidence to create: {item.evidence_to_create}",
                    "Success criteria:",
                    *[f"- {criterion}" for criterion in item.success_criteria],
                    "",
                ]
            )
    if result.missing_evidence_warnings:
        lines.append("## Missing Evidence Warnings")
        lines.extend(f"- {warning}" for warning in result.missing_evidence_warnings)
        lines.append("")
    if result.cautions:
        lines.append("## Cautions")
        lines.extend(f"- {caution}" for caution in result.cautions)
    return "\n".join(lines)


def application_materials_markdown(result: ApplicationMaterialsResult) -> str:
    lines = ["# Snipe Application Materials", "", result.summary, ""]
    lines.extend(["## Cover Letter", result.cover_letter, ""])
    lines.extend(["## Concise Cover Note", result.concise_cover_note, ""])
    lines.extend(["## Email Application", result.email_application, ""])
    if result.evidence_used:
        lines.append("## Evidence Used")
        lines.extend(f"- {item}" for item in result.evidence_used)
        lines.append("")
    if result.missing_evidence_warnings:
        lines.append("## Missing Evidence Warnings")
        lines.extend(f"- {warning}" for warning in result.missing_evidence_warnings)
        lines.append("")
    if result.cautions:
        lines.append("## Cautions")
        lines.extend(f"- {caution}" for caution in result.cautions)
    return "\n".join(lines)
