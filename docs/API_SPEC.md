# API Spec

## Conventions

- Base path: `/api/v1`.
- Authentication: Supabase Auth JWT passed to the FastAPI backend.
- Request and response schemas: Pydantic.
- Validation errors: structured JSON with field-level details.
- Long-running or expensive AI outputs should return a job/status pattern when needed.
- Endpoints must enforce user ownership for every profile, source, analysis, and generated output.

## Health

### GET `/health`

Returns backend status, version, and dependency health where safe.

## Profiles

### POST `/profiles`

Creates a candidate profile shell with career goal and preferred role.

Body:

- career_goal.
- preferred_role.
- target_specialization.
- target_seniority.
- location_preference.
- remote_preference.

### GET `/profiles`

Lists the current user's profiles.

### GET `/profiles/{profile_id}`

Returns normalized candidate profile summary, completeness, sources, latest scores, and available outputs.

### PATCH `/profiles/{profile_id}`

Updates user-controlled profile fields such as career goal, preferred role, target specialization, availability, and location preference.

### DELETE `/profiles/{profile_id}`

Deletes profile data according to the delete-my-data policy.

## Sources

### POST `/profiles/{profile_id}/sources/resume`

Uploads the required resume file.

Supported file types:

- PDF.
- DOCX.

Responsibilities:

- Store file privately.
- Parse text.
- Build or update normalized profile.
- Create evidence records.
- Run deterministic resume validation.

### POST `/profiles/{profile_id}/sources/linkedin`

Phase 2 endpoint for LinkedIn PDF, export, or pasted content.

Direct LinkedIn scraping is not supported.

### POST `/profiles/{profile_id}/sources/github`

Phase 2 endpoint for public GitHub profile URL or username.

Uses GitHub REST API and public data only.

### POST `/profiles/{profile_id}/sources/portfolio`

Phase 2 endpoint for portfolio URL or uploaded portfolio material.

Uses HTTPX and BeautifulSoup or Trafilatura for extraction where allowed.

### GET `/profiles/{profile_id}/sources`

Lists sources, parsing status, retention policy, and hashes.

### DELETE `/profiles/{profile_id}/sources/{source_id}`

Deletes or detaches a source and triggers profile re-evaluation if needed.

## Analysis

### POST `/profiles/{profile_id}/analyses/resume-quality`

Runs resume-quality analysis.

MVP. Primarily deterministic with optional AI explanation.

### POST `/profiles/{profile_id}/analyses/ats-readiness`

Runs platform-defined ATS-readiness scoring.

Body may include:

- job_description_id.
- target_role.

### POST `/profiles/{profile_id}/analyses/specialization`

Detects primary and secondary specialization, estimated seniority, confidence, and evidence.

### POST `/profiles/{profile_id}/analyses/readiness-dashboard`

Generates career-readiness dashboard scores from current profile and available analyses.

### POST `/profiles/{profile_id}/analyses/profile-completeness`

Runs platform-defined profile-completeness scoring.

## Job Descriptions

### POST `/profiles/{profile_id}/job-descriptions`

Creates a target job description from pasted text or uploaded document.

Extracts:

- Required skills.
- Preferred skills.
- Responsibilities.
- Experience requirements.
- Education requirements.
- Tools and technologies.
- Soft skills.
- Seniority expectations.
- ATS keywords.

### GET `/profiles/{profile_id}/job-descriptions`

Lists target job descriptions.

### POST `/profiles/{profile_id}/job-descriptions/upload`

Creates a target job description from an uploaded PDF or DOCX document.

### POST `/profiles/{profile_id}/analyses/skill-gap`

Runs deterministic skill-gap comparison with optional AI explanation.

### POST `/profiles/{profile_id}/job-matches`

Phase 3 endpoint for job match scoring and explanation.

### GET `/profiles/{profile_id}/job-matches`

Lists saved deterministic job-match runs.

### GET `/profiles/{profile_id}/job-matches/{analysis_id}`

Returns a saved deterministic job-match run.

## Generated Outputs

All generation endpoints must:

- Use cached output when input hash matches.
- Use structured profile facts rather than raw documents.
- Avoid fabricating unsupported facts.
- Return evidence references when applicable.

### POST `/profiles/{profile_id}/ai/resume-rewrite-suggestions`

Phase 2. Rewrites selected resume bullets.

### POST `/profiles/{profile_id}/ai/readiness-interpretation`

Phase 2. Generates or improves profile summaries.

### POST `/profiles/{profile_id}/ai/linkedin`

Phase 2. Generates requested LinkedIn sections.

### POST `/profiles/{profile_id}/ai/application-materials`

Phase 2. Generates selected cover letter format.

### POST `/profiles/{profile_id}/ai/resume-tailoring-package`

Phase 2. Generates job-specific resume tailoring recommendations.

### POST `/profiles/{profile_id}/ai/project-roadmap-recommendations`

Phase 2. Generates personalized project recommendations.

### POST `/profiles/{profile_id}/ai/project-roadmap-recommendations`

Phase 2. Generates 7-day, 30-day, 90-day, or six-month roadmap.

### POST `/profiles/{profile_id}/ai/learning-plan`

Phase 2. Generates daily, weekly, or monthly plan.

### POST `/profiles/{profile_id}/ai/outreach-message-pack`

Phase 3. Generates outreach content.

## Interview

### POST `/profiles/{profile_id}/interview/questions`

Phase 3. Generates personalized interview questions.

### POST `/profiles/{profile_id}/interview/sessions`

Phase 3. Starts a mock interview session.

### POST `/profiles/{profile_id}/interview/sessions/messages`

Phase 3. Sends an answer and receives evaluation plus follow-up.

### POST `/profiles/{profile_id}/interview/answer-evaluation`

Phase 3. Evaluates a standalone answer.

### POST `/profiles/{profile_id}/ai/claim-verification-questions`

Phase 3. Generates claim verification questions and evidence-strength notes. Must not describe the system as lie detection.

## Reports

### POST `/profiles/{profile_id}/reports/basic`

Generates a downloadable career report.

MVP includes:

- Candidate summary.
- Detected specializations.
- Confidence scores.
- Career-readiness scores.
- Resume findings.
- ATS analysis.
- Strengths.
- Weaknesses.
- Skill gaps.

Later phases add:

- Job matches.
- Recommended projects.
- Career roadmap.
- Interview questions.
- LinkedIn recommendations.

### POST `/profiles/{profile_id}/reports/full`

Generates a full report from available analyses and saved generated outputs.

## RAG

### POST `/rag/documents`

Ingests a reference document for job listings, job descriptions, role frameworks, or career guidance.

### GET `/rag/documents`

Lists saved RAG reference documents.

### PUT `/rag/documents/{document_id}`

Replaces a saved RAG reference and rebuilds its chunks.

### DELETE `/rag/documents/{document_id}`

Deletes a saved RAG reference and its chunks.

### POST `/rag/search`

Searches RAG references, optionally filtered by source type.

### POST `/rag/jobs/search`

Searches only job listing and job description references.

## Saved Outputs

### GET `/profiles/{profile_id}/generated-outputs`

Lists completed generated outputs.

### GET `/profiles/{profile_id}/generated-outputs/{output_id}`

Returns one generated output.

### DELETE `/profiles/{profile_id}/generated-outputs/{output_id}`

Deletes one generated output.

## Privacy

### GET `/profiles/{profile_id}/privacy/data-summary`

Shows what user data is stored.

### DELETE `/profiles/{profile_id}/privacy/documents`

Deletes raw uploaded documents while retaining allowed parsed profile facts, if selected by the user.

### DELETE `/profiles/{profile_id}/privacy`

Deletes the user's application data according to the product policy.

## Admin Or Internal Endpoints

Admin endpoints should be avoided in MVP unless necessary. Future internal endpoints may support RAG ingestion, taxonomy updates, and scoring-rule versioning.
