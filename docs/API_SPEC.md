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

### POST `/profiles/{profile_id}/analyses/resume`

Runs resume-quality analysis.

MVP. Primarily deterministic with optional AI explanation.

### POST `/profiles/{profile_id}/analyses/ats`

Runs platform-defined ATS-readiness scoring.

Body may include:

- job_description_id.
- target_role.

### POST `/profiles/{profile_id}/analyses/specialization`

Detects primary and secondary specialization, estimated seniority, confidence, and evidence.

### POST `/profiles/{profile_id}/analyses/readiness`

Generates career-readiness dashboard scores from current profile and available analyses.

### GET `/profiles/{profile_id}/analyses`

Lists analysis history.

### GET `/profiles/{profile_id}/analyses/{analysis_id}`

Returns one analysis result.

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

### GET `/profiles/{profile_id}/job-descriptions/{job_description_id}`

Returns structured job description.

### POST `/profiles/{profile_id}/job-descriptions/{job_description_id}/skill-gap`

Runs deterministic skill-gap comparison with optional AI explanation.

### POST `/profiles/{profile_id}/job-descriptions/{job_description_id}/match`

Phase 3 endpoint for job match scoring and explanation.

## Generated Outputs

All generation endpoints must:

- Use cached output when input hash matches.
- Use structured profile facts rather than raw documents.
- Avoid fabricating unsupported facts.
- Return evidence references when applicable.

### POST `/profiles/{profile_id}/generate/resume-bullets`

Phase 2. Rewrites selected resume bullets.

### POST `/profiles/{profile_id}/generate/professional-summary`

Phase 2. Generates or improves profile summaries.

### POST `/profiles/{profile_id}/generate/linkedin`

Phase 2. Generates requested LinkedIn sections.

### POST `/profiles/{profile_id}/job-descriptions/{job_description_id}/generate/cover-letter`

Phase 2. Generates selected cover letter format.

### POST `/profiles/{profile_id}/job-descriptions/{job_description_id}/generate/resume-tailoring`

Phase 2. Generates job-specific resume tailoring recommendations.

### POST `/profiles/{profile_id}/generate/projects`

Phase 2. Generates personalized project recommendations.

### POST `/profiles/{profile_id}/generate/roadmap`

Phase 2. Generates 7-day, 30-day, 90-day, or six-month roadmap.

### POST `/profiles/{profile_id}/generate/learning-plan`

Phase 2. Generates daily, weekly, or monthly plan.

### POST `/profiles/{profile_id}/generate/recruiter-outreach`

Phase 3. Generates outreach content.

## Interview

### POST `/profiles/{profile_id}/interview/questions`

Phase 3. Generates personalized interview questions.

### POST `/profiles/{profile_id}/interview/sessions`

Phase 3. Starts a mock interview session.

### POST `/profiles/{profile_id}/interview/sessions/{session_id}/messages`

Phase 3. Sends an answer and receives evaluation plus follow-up.

### POST `/profiles/{profile_id}/interview/answer-evaluation`

Phase 3. Evaluates a standalone answer.

### POST `/profiles/{profile_id}/interview/claim-verification`

Phase 3. Generates claim verification questions and evidence-strength notes. Must not describe the system as lie detection.

## Reports

### POST `/profiles/{profile_id}/reports`

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

### GET `/profiles/{profile_id}/reports`

Lists reports.

### GET `/profiles/{profile_id}/reports/{report_id}/download`

Returns a signed download URL or streams the report after ownership checks.

## Privacy

### GET `/privacy/data-summary`

Shows what user data is stored.

### POST `/privacy/delete-documents`

Deletes raw uploaded documents while retaining allowed parsed profile facts, if selected by the user.

### POST `/privacy/delete-my-data`

Deletes the user's application data according to the product policy.

## Admin Or Internal Endpoints

Admin endpoints should be avoided in MVP unless necessary. Future internal endpoints may support RAG ingestion, taxonomy updates, and scoring-rule versioning.
