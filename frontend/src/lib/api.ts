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
