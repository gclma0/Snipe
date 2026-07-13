export type CandidateProfile = {
  id: string;
  career_goal: string | null;
  preferred_role: string | null;
  profile_status: string;
};

export type ResumeUploadResult = {
  source_id: string | null;
  profile_id: string;
  source_type: string;
  original_filename: string;
  storage_path: string;
  content_hash: string;
  parsed_text_hash: string;
  parser_version: string;
  status: string;
  text_length: number;
  page_count: number | null;
  paragraph_count: number | null;
  profile_version: number | null;
  evidence_count: number;
  normalized_profile_updated: boolean;
};

export type ResumeQualityFinding = {
  code: string;
  severity: "info" | "low" | "medium" | "high";
  title: string;
  detail: string;
  recommendation: string;
};

export type ResumeQualityResult = {
  analysis_type: string;
  deterministic_version: string;
  score: number;
  findings: ResumeQualityFinding[];
  checks: Record<string, boolean>;
};

export type DeterministicScoreResult = ResumeQualityResult;

export type StructuredJobDescription = {
  parser_version: string;
  title: string | null;
  company: string | null;
  required_skills: string[];
  preferred_skills: string[];
  tools: string[];
  soft_skills: string[];
  responsibilities: string[];
  education: string[];
  experience_requirements: string[];
  seniority: string | null;
  ats_keywords: string[];
};

export type JobDescriptionResult = {
  id: string | null;
  profile_id: string;
  source_type: string;
  input_hash: string;
  structured: StructuredJobDescription;
};

export type SkillGapItem = {
  skill: string;
  category: string;
  importance: string;
  evidence: string | null;
};

export type SkillGapResult = {
  analysis_type: string;
  deterministic_version: string;
  score: number;
  matched_skills: SkillGapItem[];
  partially_matched_skills: SkillGapItem[];
  missing_skills: SkillGapItem[];
  transferable_skills: SkillGapItem[];
  claimed_but_unverified_skills: SkillGapItem[];
  not_relevant_skills: SkillGapItem[];
  checks: Record<string, boolean>;
};

export type SpecializationSignal = {
  name: string;
  confidence: number;
  evidence: string[];
};

export type ReadinessDashboardResult = {
  analysis_type: string;
  deterministic_version: string;
  scores: {
    overall: number;
    resume_quality: number;
    ats_readiness: number;
    skill_alignment: number | null;
    profile_completeness: number;
  };
  interpretation: {
    interpreter_version: string;
    primary_specialization: SpecializationSignal | null;
    secondary_specializations: SpecializationSignal[];
    estimated_seniority: string | null;
    seniority_confidence: number;
    evidence: string[];
  };
  skill_gap: SkillGapResult | null;
  checks: Record<string, boolean>;
};

export type BasicReportResult = {
  report_type: string;
  report_version: string;
  title: string;
  summary: string;
  readiness: ReadinessDashboardResult;
  strengths: string[];
  weaknesses: string[];
  skill_gaps: string[];
  markdown: string;
};

export type FullCareerReportResult = {
  report_type: string;
  report_version: string;
  title: string;
  summary: string;
  sections_included: string[];
  markdown: string;
};

export type AIRecommendation = {
  title: string;
  rationale: string;
  action: string;
  priority: "high" | "medium" | "low";
};

export type AIInterpretationResult = {
  output_type: string;
  output_version: string;
  provider: string;
  model_name: string;
  summary: string;
  readiness_explanation: string;
  recommendations: AIRecommendation[];
  cautions: string[];
  cached: boolean;
};

export type ResumeRewriteSuggestion = {
  original: string;
  suggested: string;
  rationale: string;
  evidence_used: string[];
  needs_candidate_value: boolean;
};

export type ResumeRewriteResult = {
  output_type: string;
  output_version: string;
  provider: string;
  model_name: string;
  summary: string;
  suggestions: ResumeRewriteSuggestion[];
  cautions: string[];
  cached: boolean;
};

export type KeywordInsertionRecommendation = {
  keyword: string;
  placement: string;
  reason: string;
  evidence_status: "verified" | "missing_evidence";
};

export type ResumeTailoringPackageResult = {
  output_type: string;
  output_version: string;
  provider: string;
  model_name: string;
  summary: string;
  tailored_summary: string;
  skill_order: string[];
  keyword_recommendations: KeywordInsertionRecommendation[];
  missing_evidence_warnings: string[];
  cautions: string[];
  cached: boolean;
};

export type InterviewQuestion = {
  category:
    | "role_specific"
    | "technical"
    | "behavioral"
    | "situational"
    | "resume_based"
    | "project_based"
    | "portfolio_based"
    | "leadership"
    | "career_transition"
    | "job_specific"
    | "screening";
  question: string;
  why_it_matters: string;
  answer_guidance: string;
  evidence_to_use: string[];
  missing_evidence_warning: string | null;
};

export type InterviewPrepResult = {
  output_type: string;
  output_version: string;
  provider: string;
  model_name: string;
  summary: string;
  questions: InterviewQuestion[];
  star_guidance: string[];
  missing_evidence_warnings: string[];
  cautions: string[];
  cached: boolean;
};

export type ClaimQuestion = {
  claim: string;
  evidence_strength: "strong" | "moderate" | "needs_clarification" | "missing";
  question: string;
  why_it_matters: string;
  evidence_to_prepare: string[];
  caution: string | null;
};

export type ClaimVerificationResult = {
  output_type: string;
  output_version: string;
  provider: string;
  model_name: string;
  summary: string;
  questions: ClaimQuestion[];
  evidence_strength_notes: string[];
  cautions: string[];
  cached: boolean;
};

export type AnswerEvaluationResult = {
  output_type: string;
  output_version: string;
  relevance_score: number;
  clarity_score: number;
  evidence_score: number;
  depth_score: number;
  confidence_score: number;
  overall_score: number;
  star_feedback: string[];
  strengths: string[];
  improvements: string[];
  improved_answer: string;
  follow_up_question: string;
  cautions: string[];
};

export type MockInterviewQuestion = {
  category: string;
  question: string;
  evidence_to_use: string[];
};

export type MockInterviewTranscriptItem = {
  question: MockInterviewQuestion;
  answer: string;
  evaluation: AnswerEvaluationResult;
  follow_up_question: string;
};

export type MockInterviewSession = {
  session_id: string;
  version: string;
  status: "active" | "completed";
  current_index: number;
  questions: MockInterviewQuestion[];
  transcript: MockInterviewTranscriptItem[];
};

export type MockInterviewTurnResult = {
  session: MockInterviewSession;
  evaluation: AnswerEvaluationResult;
  follow_up_question: string;
  next_question: MockInterviewQuestion | null;
};

export type OutreachMessagePack = {
  output_type: string;
  output_version: string;
  provider: string;
  model_name: string;
  summary: string;
  linkedin_connection_message: string;
  recruiter_outreach_message: string;
  job_application_email: string;
  follow_up_email: string;
  interview_thank_you_email: string;
  referral_request: string;
  short_professional_intro: string;
  evidence_used: string[];
  missing_evidence_warnings: string[];
  cautions: string[];
  cached: boolean;
};

export type CareerTransitionResult = {
  output_type: string;
  output_version: string;
  provider: string;
  model_name: string;
  summary: string;
  transferable_skills: string[];
  reframed_experience: string[];
  missing_foundational_knowledge: string[];
  transitional_roles: string[];
  recommended_projects: string[];
  learning_sequence: string[];
  resume_positioning: string[];
  likely_interview_concerns: string[];
  cautions: string[];
  cached: boolean;
};

export type ProjectRecommendation = {
  title: string;
  objective: string;
  skills_practiced: string[];
  deliverables: string[];
  evidence_to_add: string[];
  missing_evidence_warning: string | null;
};

export type RoadmapStep = {
  timeframe: "7_day" | "30_day" | "90_day";
  focus: string;
  actions: string[];
  success_criteria: string[];
};

export type ProjectRoadmapResult = {
  output_type: string;
  output_version: string;
  provider: string;
  model_name: string;
  summary: string;
  projects: ProjectRecommendation[];
  roadmap: RoadmapStep[];
  missing_evidence_warnings: string[];
  cautions: string[];
  cached: boolean;
};

export type LearningPlanStep = {
  cadence: "daily" | "weekly" | "monthly";
  title: string;
  tasks: string[];
  practice_activity: string;
  evidence_to_create: string;
  success_criteria: string[];
};

export type LearningPlanResult = {
  output_type: string;
  output_version: string;
  provider: string;
  model_name: string;
  summary: string;
  daily_plan: LearningPlanStep[];
  weekly_plan: LearningPlanStep[];
  monthly_plan: LearningPlanStep[];
  missing_evidence_warnings: string[];
  cautions: string[];
  cached: boolean;
};

export type LinkedInExperienceRecommendation = {
  section: string;
  recommendation: string;
  evidence_to_use: string[];
  missing_evidence_warning: string | null;
};

export type LinkedInOptimizationResult = {
  output_type: string;
  output_version: string;
  provider: string;
  model_name: string;
  summary: string;
  headline_options: string[];
  about_section: string;
  experience_recommendations: LinkedInExperienceRecommendation[];
  skills_to_feature: string[];
  profile_checklist: string[];
  missing_evidence_warnings: string[];
  cautions: string[];
  cached: boolean;
};

export type ApplicationMaterialsResult = {
  output_type: string;
  output_version: string;
  provider: string;
  model_name: string;
  summary: string;
  cover_letter: string;
  concise_cover_note: string;
  email_application: string;
  evidence_used: string[];
  missing_evidence_warnings: string[];
  cautions: string[];
  cached: boolean;
};

export type JobMatch = {
  job_reference_id: string;
  title: string;
  company: string | null;
  match_score: number;
  semantic_score: number;
  skill_alignment_score: number;
  matched_skills: string[];
  partially_matched_skills: string[];
  missing_skills: string[];
  relevant_experience: string[];
  concerns: string[];
  explanation: string;
  apply_recommendation: "strong_apply" | "apply_with_tailoring" | "build_evidence_first";
  structured_job: StructuredJobDescription;
  source_excerpt: string;
  citation: {
    document_id: string;
    chunk_id: string | null;
    title: string;
    source_type: string;
    source_url: string | null;
    score: number;
  };
};

export type JobMatchResult = {
  analysis_type: string;
  deterministic_version: string;
  query: string;
  match_count: number;
  matches: JobMatch[];
  checks: Record<string, boolean>;
};

export type SavedJobMatchRun = {
  id: string;
  analysis_type: string;
  query: string;
  match_count: number;
  top_match_title: string | null;
  top_match_score: number | null;
  created_at: string | null;
  result: JobMatchResult;
};

export type GeneratedOutput = {
  id: string;
  output_type: string;
  job_description_id: string | null;
  prompt_version: string | null;
  provider: string | null;
  model_name: string | null;
  result_json: Record<string, unknown>;
  result_markdown: string | null;
  status: string;
  created_at: string | null;
};

export type ProfileDeletionResult = {
  profile_id: string;
  deleted: boolean;
  deleted_storage_objects: number;
};

export type PrivacyDataSummaryResult = {
  profile_id: string;
  profile_exists: boolean;
  stored_document_count: number;
  generated_output_count: number;
  retention_policy: string;
};

export type DocumentDeletionResult = {
  profile_id: string;
  deleted_storage_objects: number;
  profile_retained: boolean;
};

export type GitHubSourceResult = {
  source_id: string | null;
  profile_id: string;
  username: string;
  status: string;
  repository_count: number;
  analyzed_repository_count: number;
  primary_languages: string[];
  readme_repository_count: number;
  test_signal_count: number;
  ci_signal_count: number;
  notable_repositories: string[];
  evidence_count: number;
  profile_version: number | null;
};

export type PortfolioSourceResult = {
  source_id: string | null;
  profile_id: string;
  url: string;
  status: string;
  title: string | null;
  technical_signals: string[];
  non_technical_signals: string[];
  project_signal_count: number;
  contact_signal_count: number;
  evidence_count: number;
  profile_version: number | null;
};

export type LinkedInSourceResult = {
  source_id: string | null;
  profile_id: string;
  source_type: string;
  status: string;
  headline: string | null;
  skill_signals: string[];
  experience_count: number;
  evidence_count: number;
  profile_version: number | null;
};

export type RagSourceType = "job_description" | "role_framework" | "career_guidance" | "job_listing";

export type RagDocumentResult = {
  document_id: string | null;
  title: string;
  source_type: RagSourceType;
  content_hash: string;
  chunk_count: number;
  embedding_model: string;
};

export type RagDocumentSummary = {
  document_id: string;
  title: string;
  source_type: RagSourceType;
  source_url: string | null;
  content_hash: string;
  embedding_model: string;
  metadata: Record<string, unknown>;
  created_at: string | null;
};

export type RagDocumentDeletionResult = {
  document_id: string;
  deleted: boolean;
};

export type RagCitation = {
  document_id: string;
  chunk_id: string | null;
  title: string;
  source_type: RagSourceType;
  source_url: string | null;
  chunk_index: number;
  content: string;
  score: number;
  metadata: Record<string, unknown>;
};

export type RagSearchResult = {
  query: string;
  embedding_model: string;
  citations: RagCitation[];
};
