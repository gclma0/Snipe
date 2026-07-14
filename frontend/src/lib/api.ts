import { env } from "@/lib/env";

export type {
  CandidateProfile,
  ResumeUploadResult,
  ResumeQualityFinding,
  ResumeQualityResult,
  DeterministicScoreResult,
  StructuredJobDescription,
  JobDescriptionResult,
  SkillGapItem,
  SkillGapResult,
  SpecializationSignal,
  ReadinessDashboardResult,
  BasicReportResult,
  FullCareerReportResult,
  AIRecommendation,
  AIInterpretationResult,
  ResumeRewriteSuggestion,
  ResumeRewriteResult,
  KeywordInsertionRecommendation,
  ResumeTailoringPackageResult,
  InterviewQuestion,
  InterviewPrepResult,
  ClaimQuestion,
  ClaimVerificationResult,
  AnswerEvaluationResult,
  MockInterviewQuestion,
  MockInterviewTranscriptItem,
  MockInterviewSession,
  MockInterviewTurnResult,
  OutreachMessagePack,
  CareerTransitionResult,
  ProjectRecommendation,
  RoadmapStep,
  ProjectRoadmapResult,
  LearningPlanStep,
  LearningPlanResult,
  LinkedInExperienceRecommendation,
  LinkedInOptimizationResult,
  ApplicationMaterialsResult,
  JobMatch,
  JobMatchResult,
  SavedJobMatchRun,
  GeneratedOutput,
  ProfileDeletionResult,
  PrivacyDataSummaryResult,
  PrivacyEvent,
  ProfileDataExportResult,
  DocumentDeletionResult,
  GitHubSourceResult,
  PortfolioSourceResult,
  LinkedInSourceResult,
  RagDocumentDeletionResult,
  RagDocumentResult,
  RagDocumentSummary,
  RagSearchResult,
  RagSourceType,
  AIProviderStatus,
} from "./apiTypes";

import type {
  CandidateProfile,
  ResumeUploadResult,
  ResumeQualityResult,
  DeterministicScoreResult,
  JobDescriptionResult,
  SkillGapResult,
  ReadinessDashboardResult,
  BasicReportResult,
  FullCareerReportResult,
  AIInterpretationResult,
  ResumeRewriteResult,
  ResumeTailoringPackageResult,
  InterviewPrepResult,
  ClaimVerificationResult,
  AnswerEvaluationResult,
  MockInterviewSession,
  MockInterviewTurnResult,
  OutreachMessagePack,
  CareerTransitionResult,
  ProjectRoadmapResult,
  LearningPlanResult,
  LinkedInOptimizationResult,
  ApplicationMaterialsResult,
  JobMatchResult,
  SavedJobMatchRun,
  GeneratedOutput,
  ProfileDeletionResult,
  PrivacyDataSummaryResult,
  PrivacyEvent,
  ProfileDataExportResult,
  DocumentDeletionResult,
  GitHubSourceResult,
  PortfolioSourceResult,
  LinkedInSourceResult,
  RagDocumentDeletionResult,
  RagDocumentResult,
  RagDocumentSummary,
  RagSearchResult,
  RagSourceType,
  AIProviderStatus,
} from "./apiTypes";

const REQUEST_ID_HEADER = "X-Request-ID";

export class ApiError extends Error {
  requestId: string | null;
  status: number;

  constructor(message: string, options: { requestId: string | null; status: number }) {
    super(formatApiErrorMessage(message, options.requestId));
    this.name = "ApiError";
    this.requestId = options.requestId;
    this.status = options.status;
  }
}

async function publicRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${env.apiBaseUrl}${path}`, init);

  if (!response.ok) {
    throw await apiErrorFromResponse(response);
  }

  return response.json() as Promise<T>;
}

async function request<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${env.apiBaseUrl}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    throw await apiErrorFromResponse(response);
  }

  return response.json() as Promise<T>;
}

async function apiErrorFromResponse(response: Response) {
  const error = await response.json().catch(() => ({ detail: response.statusText }));
  const message = typeof error.detail === "string" ? error.detail : "Request failed.";
  return new ApiError(message, {
    requestId: response.headers.get(REQUEST_ID_HEADER),
    status: response.status,
  });
}

function formatApiErrorMessage(message: string, requestId: string | null) {
  if (!requestId) {
    return message;
  }
  return `${message} Request ID: ${requestId}`;
}

export function getAIProviderStatus() {
  return publicRequest<AIProviderStatus>("/health/ai-provider");
}

export function listProfiles(token: string) {
  return request<CandidateProfile[]>("/profiles", token);
}

export function createProfile(token: string, payload: { career_goal: string; preferred_role: string }) {
  return request<CandidateProfile>("/profiles", token, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
}

export function uploadResume(
  token: string,
  profileId: string,
  file: File,
  deleteAfterParsing = false,
) {
  const body = new FormData();
  body.append("file", file);
  body.append("delete_after_parsing", String(deleteAfterParsing));
  return request<ResumeUploadResult>(`/profiles/${profileId}/sources/resume`, token, {
    method: "POST",
    body,
  });
}

export function runResumeQualityAnalysis(token: string, profileId: string) {
  return request<ResumeQualityResult>(`/profiles/${profileId}/analyses/resume-quality`, token, {
    method: "POST",
  });
}

export function runAtsReadinessAnalysis(token: string, profileId: string) {
  return request<DeterministicScoreResult>(`/profiles/${profileId}/analyses/ats-readiness`, token, {
    method: "POST",
  });
}

export function runProfileCompletenessAnalysis(token: string, profileId: string) {
  return request<DeterministicScoreResult>(`/profiles/${profileId}/analyses/profile-completeness`, token, {
    method: "POST",
  });
}

export function createJobDescription(token: string, profileId: string, text: string) {
  return request<JobDescriptionResult>(`/profiles/${profileId}/job-descriptions`, token, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text }),
  });
}

export function uploadJobDescription(token: string, profileId: string, file: File) {
  const body = new FormData();
  body.append("file", file);
  return request<JobDescriptionResult>(`/profiles/${profileId}/job-descriptions/upload`, token, {
    method: "POST",
    body,
  });
}

export function listJobDescriptions(token: string, profileId: string) {
  return request<JobDescriptionResult[]>(`/profiles/${profileId}/job-descriptions`, token);
}

export function runSkillGapAnalysis(token: string, profileId: string, jobDescriptionId: string) {
  return request<SkillGapResult>(`/profiles/${profileId}/analyses/skill-gap`, token, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ job_description_id: jobDescriptionId }),
  });
}

export function runReadinessDashboard(
  token: string,
  profileId: string,
  jobDescriptionId?: string | null,
) {
  return request<ReadinessDashboardResult>(`/profiles/${profileId}/analyses/readiness-dashboard`, token, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ job_description_id: jobDescriptionId ?? null }),
  });
}

export function runJobMatches(
  token: string,
  profileId: string,
  query?: string | null,
  limit = 10,
) {
  return request<JobMatchResult>(`/profiles/${profileId}/job-matches`, token, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query: query || null, limit }),
  });
}

export function listSavedJobMatches(token: string, profileId: string, limit = 20) {
  return request<SavedJobMatchRun[]>(
    `/profiles/${profileId}/job-matches?limit=${encodeURIComponent(String(limit))}`,
    token,
  );
}

export function getSavedJobMatch(token: string, profileId: string, analysisId: string) {
  return request<SavedJobMatchRun>(
    `/profiles/${profileId}/job-matches/${encodeURIComponent(analysisId)}`,
    token,
  );
}

export function createBasicReport(
  token: string,
  profileId: string,
  jobDescriptionId?: string | null,
) {
  return request<BasicReportResult>(`/profiles/${profileId}/reports/basic`, token, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ job_description_id: jobDescriptionId ?? null }),
  });
}

export function createFullReport(
  token: string,
  profileId: string,
  jobDescriptionId?: string | null,
) {
  return request<FullCareerReportResult>(`/profiles/${profileId}/reports/full`, token, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ job_description_id: jobDescriptionId ?? null }),
  });
}

export function createAIReadinessInterpretation(
  token: string,
  profileId: string,
  jobDescriptionId?: string | null,
  forceRegenerate = false,
) {
  return request<AIInterpretationResult>(`/profiles/${profileId}/ai/readiness-interpretation`, token, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      job_description_id: jobDescriptionId ?? null,
      force_regenerate: forceRegenerate,
    }),
  });
}

export function createResumeRewriteSuggestions(
  token: string,
  profileId: string,
  jobDescriptionId?: string | null,
  forceRegenerate = false,
) {
  return request<ResumeRewriteResult>(`/profiles/${profileId}/ai/resume-rewrite-suggestions`, token, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      job_description_id: jobDescriptionId ?? null,
      force_regenerate: forceRegenerate,
    }),
  });
}

export function createResumeTailoringPackage(
  token: string,
  profileId: string,
  jobDescriptionId?: string | null,
  forceRegenerate = false,
) {
  return request<ResumeTailoringPackageResult>(`/profiles/${profileId}/ai/resume-tailoring-package`, token, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      job_description_id: jobDescriptionId ?? null,
      force_regenerate: forceRegenerate,
    }),
  });
}

export function createInterviewPrep(
  token: string,
  profileId: string,
  jobDescriptionId?: string | null,
  forceRegenerate = false,
) {
  return request<InterviewPrepResult>(`/profiles/${profileId}/ai/interview-prep`, token, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      job_description_id: jobDescriptionId ?? null,
      force_regenerate: forceRegenerate,
    }),
  });
}

export function createClaimVerificationQuestions(
  token: string,
  profileId: string,
  jobDescriptionId?: string | null,
  forceRegenerate = false,
) {
  return request<ClaimVerificationResult>(`/profiles/${profileId}/ai/claim-verification-questions`, token, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      job_description_id: jobDescriptionId ?? null,
      force_regenerate: forceRegenerate,
    }),
  });
}

export function startMockInterview(
  token: string,
  profileId: string,
  jobDescriptionId?: string | null,
  questionCount = 5,
) {
  return request<MockInterviewSession>(`/profiles/${profileId}/interview/sessions`, token, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      job_description_id: jobDescriptionId ?? null,
      question_count: questionCount,
    }),
  });
}

export function answerMockInterview(
  token: string,
  profileId: string,
  session: MockInterviewSession,
  answer: string,
) {
  return request<MockInterviewTurnResult>(`/profiles/${profileId}/interview/sessions/messages`, token, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ session, answer }),
  });
}

export function evaluateInterviewAnswer(
  token: string,
  profileId: string,
  payload: {
    question: string;
    answer: string;
    evidence_to_use?: string[];
    category?: string | null;
  },
) {
  return request<AnswerEvaluationResult>(`/profiles/${profileId}/interview/answer-evaluation`, token, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      ...payload,
      evidence_to_use: payload.evidence_to_use ?? [],
      category: payload.category ?? null,
    }),
  });
}

export function createOutreachMessagePack(
  token: string,
  profileId: string,
  jobDescriptionId?: string | null,
) {
  return request<OutreachMessagePack>(`/profiles/${profileId}/ai/outreach-message-pack`, token, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ job_description_id: jobDescriptionId ?? null }),
  });
}

export function createCareerTransitionAnalysis(
  token: string,
  profileId: string,
  jobDescriptionId?: string | null,
) {
  return request<CareerTransitionResult>(`/profiles/${profileId}/ai/career-transition-analysis`, token, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ job_description_id: jobDescriptionId ?? null }),
  });
}

export function createProjectRoadmap(
  token: string,
  profileId: string,
  jobDescriptionId?: string | null,
  forceRegenerate = false,
) {
  return request<ProjectRoadmapResult>(
    `/profiles/${profileId}/ai/project-roadmap-recommendations`,
    token,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        job_description_id: jobDescriptionId ?? null,
        force_regenerate: forceRegenerate,
      }),
    },
  );
}

export function createLearningPlan(
  token: string,
  profileId: string,
  jobDescriptionId?: string | null,
  forceRegenerate = false,
) {
  return request<LearningPlanResult>(
    `/profiles/${profileId}/ai/learning-plan`,
    token,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        job_description_id: jobDescriptionId ?? null,
        force_regenerate: forceRegenerate,
      }),
    },
  );
}

export function createLinkedInOptimization(
  token: string,
  profileId: string,
  jobDescriptionId?: string | null,
  forceRegenerate = false,
) {
  return request<LinkedInOptimizationResult>(
    `/profiles/${profileId}/ai/linkedin-optimization`,
    token,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        job_description_id: jobDescriptionId ?? null,
        force_regenerate: forceRegenerate,
      }),
    },
  );
}

export function createApplicationMaterials(
  token: string,
  profileId: string,
  jobDescriptionId?: string | null,
  forceRegenerate = false,
) {
  return request<ApplicationMaterialsResult>(
    `/profiles/${profileId}/ai/application-materials`,
    token,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        job_description_id: jobDescriptionId ?? null,
        force_regenerate: forceRegenerate,
      }),
    },
  );
}

export function listGeneratedOutputs(token: string, profileId: string, limit = 20) {
  return request<GeneratedOutput[]>(
    `/profiles/${profileId}/generated-outputs?limit=${encodeURIComponent(String(limit))}`,
    token,
  );
}

export function getGeneratedOutput(token: string, profileId: string, outputId: string) {
  return request<GeneratedOutput>(
    `/profiles/${profileId}/generated-outputs/${encodeURIComponent(outputId)}`,
    token,
  );
}

export function deleteGeneratedOutput(token: string, profileId: string, outputId: string) {
  return request<{ output_id: string; deleted: boolean }>(
    `/profiles/${profileId}/generated-outputs/${encodeURIComponent(outputId)}`,
    token,
    {
      method: "DELETE",
    },
  );
}

export function deleteProfileData(token: string, profileId: string) {
  return request<ProfileDeletionResult>(`/profiles/${profileId}/privacy`, token, {
    method: "DELETE",
  });
}

export function getPrivacyDataSummary(token: string, profileId: string) {
  return request<PrivacyDataSummaryResult>(`/profiles/${profileId}/privacy/data-summary`, token);
}

export function exportProfileData(token: string, profileId: string) {
  return request<ProfileDataExportResult>(`/profiles/${profileId}/privacy/export`, token);
}

export function listPrivacyEvents(token: string, profileId: string) {
  return request<PrivacyEvent[]>(`/profiles/${profileId}/privacy/events`, token);
}

export function deleteProfileDocuments(token: string, profileId: string) {
  return request<DocumentDeletionResult>(`/profiles/${profileId}/privacy/documents`, token, {
    method: "DELETE",
  });
}

export function addGitHubSource(token: string, profileId: string, usernameOrUrl: string) {
  return request<GitHubSourceResult>(`/profiles/${profileId}/sources/github`, token, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ username_or_url: usernameOrUrl }),
  });
}

export function addPortfolioSource(token: string, profileId: string, url: string) {
  return request<PortfolioSourceResult>(`/profiles/${profileId}/sources/portfolio`, token, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ url }),
  });
}

export function addLinkedInTextSource(token: string, profileId: string, text: string) {
  return request<LinkedInSourceResult>(`/profiles/${profileId}/sources/linkedin`, token, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text }),
  });
}

export function uploadLinkedInSource(
  token: string,
  profileId: string,
  file: File,
  deleteAfterParsing = false,
) {
  const body = new FormData();
  body.append("file", file);
  body.append("delete_after_parsing", String(deleteAfterParsing));
  return request<LinkedInSourceResult>(`/profiles/${profileId}/sources/linkedin/upload`, token, {
    method: "POST",
    body,
  });
}

export function createRagDocument(
  token: string,
  payload: {
    title: string;
    source_type: RagSourceType;
    text: string;
    source_url?: string | null;
  },
) {
  return request<RagDocumentResult>("/rag/documents", token, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      ...payload,
      source_url: payload.source_url || null,
    }),
  });
}

export function listRagDocuments(token: string, limit = 20) {
  return request<RagDocumentSummary[]>(
    `/rag/documents?limit=${encodeURIComponent(String(limit))}`,
    token,
  );
}

export function deleteRagDocument(token: string, documentId: string) {
  return request<RagDocumentDeletionResult>(
    `/rag/documents/${encodeURIComponent(documentId)}`,
    token,
    {
      method: "DELETE",
    },
  );
}

export function replaceRagDocument(
  token: string,
  documentId: string,
  payload: {
    title: string;
    source_type: RagSourceType;
    text: string;
    source_url?: string | null;
  },
) {
  return request<RagDocumentResult>(
    `/rag/documents/${encodeURIComponent(documentId)}`,
    token,
    {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        ...payload,
        source_url: payload.source_url || null,
      }),
    },
  );
}

export function searchRagReferences(
  token: string,
  payload: {
    query: string;
    source_types?: RagSourceType[];
    limit?: number;
  },
) {
  return request<RagSearchResult>("/rag/search", token, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      source_types: payload.source_types ?? [],
      limit: payload.limit ?? 5,
      query: payload.query,
    }),
  });
}

export function searchJobRagReferences(
  token: string,
  payload: {
    query: string;
    limit?: number;
  },
) {
  return request<RagSearchResult>("/rag/jobs/search", token, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      source_types: ["job_description", "job_listing"],
      limit: payload.limit ?? 5,
      query: payload.query,
    }),
  });
}
