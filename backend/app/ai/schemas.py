from pydantic import BaseModel, Field


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
    category: str = Field(
        pattern=(
            "^(role_specific|technical|behavioral|situational|resume_based|project_based|"
            "portfolio_based|leadership|career_transition|job_specific|screening)$"
        )
    )
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
    questions: list[InterviewQuestion] = Field(default_factory=list, max_length=12)
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


class LearningPlanStep(BaseModel):
    cadence: str = Field(pattern="^(daily|weekly|monthly)$")
    title: str
    tasks: list[str] = Field(default_factory=list, max_length=10)
    practice_activity: str
    evidence_to_create: str
    success_criteria: list[str] = Field(default_factory=list, max_length=6)


class LearningPlanResult(BaseModel):
    output_type: str = "ai_learning_plan"
    output_version: str = "ai-learning-plan-v1"
    provider: str
    model_name: str
    summary: str
    daily_plan: list[LearningPlanStep] = Field(default_factory=list, max_length=7)
    weekly_plan: list[LearningPlanStep] = Field(default_factory=list, max_length=4)
    monthly_plan: list[LearningPlanStep] = Field(default_factory=list, max_length=6)
    missing_evidence_warnings: list[str] = Field(default_factory=list, max_length=8)
    cautions: list[str] = Field(default_factory=list, max_length=5)
    cached: bool = False


class LinkedInExperienceRecommendation(BaseModel):
    section: str
    recommendation: str
    evidence_to_use: list[str] = Field(default_factory=list, max_length=6)
    missing_evidence_warning: str | None = None


class LinkedInOptimizationResult(BaseModel):
    output_type: str = "ai_linkedin_optimization"
    output_version: str = "ai-linkedin-optimization-v1"
    provider: str
    model_name: str
    summary: str
    headline_options: list[str] = Field(default_factory=list, max_length=5)
    about_section: str
    experience_recommendations: list[LinkedInExperienceRecommendation] = Field(
        default_factory=list,
        max_length=6,
    )
    skills_to_feature: list[str] = Field(default_factory=list, max_length=20)
    profile_checklist: list[str] = Field(default_factory=list, max_length=10)
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
