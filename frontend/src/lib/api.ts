import { env } from "@/lib/env";

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

export type ProfileDeletionResult = {
  profile_id: string;
  deleted: boolean;
  deleted_storage_objects: number;
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

async function request<T>(path: string, token: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${env.apiBaseUrl}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof error.detail === "string" ? error.detail : "Request failed.");
  }

  return response.json() as Promise<T>;
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

export function uploadResume(token: string, profileId: string, file: File) {
  const body = new FormData();
  body.append("file", file);
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

export function deleteProfileData(token: string, profileId: string) {
  return request<ProfileDeletionResult>(`/profiles/${profileId}/privacy`, token, {
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

export function uploadLinkedInSource(token: string, profileId: string, file: File) {
  const body = new FormData();
  body.append("file", file);
  return request<LinkedInSourceResult>(`/profiles/${profileId}/sources/linkedin/upload`, token, {
    method: "POST",
    body,
  });
}
