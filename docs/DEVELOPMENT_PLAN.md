# Development Plan

## Phase Summary

- MVP: core profile, resume parsing, deterministic scoring, target job comparison, skill gaps, readiness dashboard, basic report, privacy baseline.
- Phase 2: optional evidence sources, profile optimization, cover letters, tailoring, project recommendations, roadmaps, learning plans, saved history, stronger caching.
- Phase 3: job retrieval and RAG matching, explainable recommendations at scale, interview workflows, recruiter outreach, career transition analysis, advanced privacy.

## Current Implementation Status

Current build status: Milestone 20 is the active milestone.

- Milestones 1-14 are implemented at usable depth.
- Milestones 15-18 are partially implemented through evidence-bound AI outputs, generated-output caching, and saved-output history.
- Milestone 19 is implemented with RAG ingestion, retrieval, source filters, and reference-library management.
- Milestone 20 is implemented for deterministic RAG-backed job matching, with saved job-match history as the remaining gap.
- Milestones 21-23 have been started ahead of strict sequence through interview prep, claim questions, mock interview, answer evaluation, outreach, and career-transition outputs.
- Milestone 24 is partially implemented through full reports and baseline privacy controls.

Known remaining gaps before Milestone 20 can be considered complete:

- Persist and reopen saved job-match runs.
- Keep API documentation aligned with the implemented routes.

Known later-phase gaps:

- Dedicated LinkedIn optimization outputs.
- Standalone daily, weekly, and monthly learning-plan generation.
- Frontend support for uploaded target job-description documents.
- Exportable user data, audit-friendly privacy events, and optional delete-after-parsing controls.

## Milestone 1: Project Foundation And Documentation Baseline

### Objective

Create the repository structure, development conventions, environment strategy, and documentation baseline without implementing application features.

### Features Included

- Documentation scaffold.
- Approved stack record.
- Product constraints.
- Phase and milestone plan.
- Architectural decisions.

### Files Or Modules Likely To Be Created

- `AGENTS.md`.
- `docs/PROJECT_SPEC.md`.
- `docs/FEATURES.md`.
- `docs/ARCHITECTURE.md`.
- `docs/DATA_MODELS.md`.
- `docs/API_SPEC.md`.
- `docs/DEVELOPMENT_PLAN.md`.
- `docs/DECISIONS.md`.
- Later implementation may add `frontend/`, `backend/`, and `.github/`.

### Dependencies

- Approved feature-list PDF.
- Approved stack and constraints.

### Tests Required

- Documentation review only.
- Verify every requested documentation file exists.
- Verify no application code has been created.

### Definition Of Done

- All requested documentation files exist.
- Full PDF scope is preserved.
- MVP, Phase 2, and Phase 3 are defined.
- Milestones are sequential and independently testable.
- Milestone 1 implementation has not started beyond documentation.

## Milestone 2: Repository And Tooling Scaffold

### Objective

Create frontend and backend project skeletons with formatting, linting, testing, and local environment configuration.

### Features Included

- No product features.
- Developer workflow foundation.

### Files Or Modules Likely To Be Created

- `frontend/`.
- `backend/`.
- `backend/app/main.py`.
- `backend/app/core/config.py`.
- `backend/tests/`.
- `frontend/src/`.
- `frontend/package.json`.
- `backend/pyproject.toml`.
- `.env.example`.
- `.github/workflows/ci.yml`.

### Dependencies

- Milestone 1.
- Node and Python tooling.

### Tests Required

- Frontend build command.
- Backend test command.
- Backend health endpoint test.
- CI workflow dry run where practical.

### Definition Of Done

- Frontend starts locally.
- Backend starts locally.
- Health endpoint works.
- CI runs lint/build/test commands.
- No product data is required.

## Milestone 3: Authentication, Storage, And Database Foundation

### Objective

Connect Supabase Auth, private storage, database migrations, and ownership rules.

### Features Included

- User authentication.
- Private file storage setup.
- Core database tables for profiles, sources, evidence, analyses, and generated outputs.

### Files Or Modules Likely To Be Created

- `backend/app/db/`.
- `backend/app/auth/`.
- `backend/app/storage/`.
- `backend/app/models/`.
- `supabase/migrations/`.
- `frontend/src/lib/supabase.ts`.
- `frontend/src/features/auth/`.

### Dependencies

- Milestone 2.
- Supabase project.

### Tests Required

- Authenticated API request test.
- Unauthorized access test.
- Storage upload permission test.
- Database migration test.
- Row-level security policy checks.

### Definition Of Done

- Users can sign in.
- Backend verifies Supabase JWTs.
- Private storage bucket exists.
- Core tables and RLS policies exist.
- Users cannot access another user's profile records.

## Milestone 4: Resume Upload And Parsing

### Objective

Implement required resume upload and deterministic parsing for PDF and DOCX.

### Features Included

- Required resume source.
- PDF parsing with PyMuPDF.
- DOCX parsing with python-docx.
- Source record creation.
- Parsed text hash and parser status.

### Files Or Modules Likely To Be Created

- `backend/app/parsing/resume_parser.py`.
- `backend/app/parsing/pdf_parser.py`.
- `backend/app/parsing/docx_parser.py`.
- `backend/app/api/routes/sources.py`.
- `frontend/src/features/profile/resume-upload.tsx`.

### Dependencies

- Milestone 3.

### Tests Required

- PDF fixture parsing.
- DOCX fixture parsing.
- Unsupported file rejection.
- Upload ownership test.
- Parser failure status test.

### Definition Of Done

- Authenticated user can upload one required resume.
- Resume is stored privately.
- Parser extracts text and basic document metadata.
- Parser status is visible to the frontend.

## Milestone 5: Normalized Candidate Profile MVP

### Objective

Convert parsed resume content and user-entered goal data into one normalized candidate profile.

### Features Included

- Career goal selection.
- Preferred role.
- Contact extraction.
- Sections.
- Skills.
- Work experience.
- Projects.
- Education.
- Certifications.
- Evidence records.

### Files Or Modules Likely To Be Created

- `backend/app/profile/profile_builder.py`.
- `backend/app/profile/evidence_builder.py`.
- `backend/app/profile/schemas.py`.
- `backend/app/api/routes/profiles.py`.
- `frontend/src/features/profile/profile-form.tsx`.
- `frontend/src/features/profile/profile-summary.tsx`.

### Dependencies

- Milestone 4.

### Tests Required

- Contact extraction tests.
- Section detection tests.
- Skill extraction tests.
- Evidence creation tests.
- Profile versioning tests.

### Definition Of Done

- Resume facts are normalized into profile records.
- Each important fact has source evidence when available.
- Profile can be retrieved through API.
- Profile version changes after resume reprocessing.

## Milestone 6: Resume Quality Analysis

### Objective

Implement deterministic resume analysis and prioritized feedback.

### Features Included

- Resume structure.
- Section completeness.
- Contact placement.
- Summary presence.
- Experience and project description checks.
- Education, skills, certifications checks.
- Date consistency.
- Bullet length.
- Weak action verbs.
- Repetitive wording.
- Formatting and readability signals.

### Files Or Modules Likely To Be Created

- `backend/app/analysis/resume_quality.py`.
- `backend/app/scoring/resume_rules.py`.
- `backend/app/api/routes/analyses.py`.
- `frontend/src/features/analysis/resume-analysis.tsx`.

### Dependencies

- Milestone 5.

### Tests Required

- Rule-level tests.
- Scoring tests.
- Prioritization tests.
- API response tests.

### Definition Of Done

- User can run resume-quality analysis.
- Findings are prioritized.
- Output is deterministic and explainable.
- No AI call is required for baseline analysis.

## Milestone 7: ATS Readiness And Profile Completeness

### Objective

Implement platform-defined ATS-readiness scoring and profile-completeness scoring.

### Features Included

- ATS-readiness score.
- Required section checks.
- Contact details.
- Keyword checks.
- Skill relevance.
- Bullet quality.
- Quantified achievement detection.
- Profile-completeness score.

### Files Or Modules Likely To Be Created

- `backend/app/scoring/ats.py`.
- `backend/app/scoring/profile_completeness.py`.
- `frontend/src/features/dashboard/readiness-scores.tsx`.

### Dependencies

- Milestone 6.

### Tests Required

- ATS scoring tests.
- Completeness scoring tests.
- Explanation generation tests.
- Guardrail test that wording does not claim commercial ATS guarantees.

### Definition Of Done

- User sees explainable ATS and completeness scores.
- Scores can run without a target job.
- Product copy says this is the platform's own ATS Readiness Score.

## Milestone 8: Target Job Description Analysis

### Objective

Support pasted or uploaded job descriptions and extract structured requirements.

### Features Included

- Paste job description.
- Upload job-description document.
- Extract required skills, preferred skills, responsibilities, experience, education, tools, soft skills, seniority, and ATS keywords.

### Files Or Modules Likely To Be Created

- `backend/app/jobs/job_parser.py`.
- `backend/app/jobs/schemas.py`.
- `backend/app/api/routes/job_descriptions.py`.
- `frontend/src/features/jobs/job-description-form.tsx`.

### Dependencies

- Milestone 7.

### Tests Required

- Job parsing fixture tests.
- Required/preferred skill extraction tests.
- API tests.
- Empty or low-quality job description validation tests.

### Definition Of Done

- User can create a structured target job description.
- Extracted requirements are visible.
- Parsing is deterministic where possible.

## Milestone 9: Skill Gap Analysis

### Objective

Compare the normalized candidate profile against a target job or role path.

### Features Included

- Matched skills.
- Partially matched skills.
- Missing skills.
- Transferable skills.
- Claimed but unverified skills.
- Not relevant skills.
- Gap urgency and importance.

### Files Or Modules Likely To Be Created

- `backend/app/matching/skill_gap.py`.
- `backend/app/taxonomy/skills.py`.
- `frontend/src/features/analysis/skill-gap.tsx`.

### Dependencies

- Milestone 8.

### Tests Required

- Skill matching tests.
- Alias normalization tests.
- Transferable skill tests.
- Gap categorization tests.

### Definition Of Done

- User can compare profile to a target job.
- Skill gaps are categorized.
- Output uses profile and job evidence.

## Milestone 10: Specialization Detection And Readiness Dashboard

### Objective

Detect specialization and seniority, then combine MVP scores into a dashboard.

### Features Included

- Primary specialization.
- Secondary specializations.
- Estimated seniority.
- Confidence score.
- Evidence.
- Overall career-readiness score.
- Resume-quality score.
- ATS-readiness score.
- Skill-alignment score.
- Profile-completeness score.

### Files Or Modules Likely To Be Created

- `backend/app/ai/profile_interpreter.py`.
- `backend/app/scoring/readiness.py`.
- `backend/app/api/routes/dashboard.py`.
- `frontend/src/features/dashboard/`.

### Dependencies

- Milestone 9.
- Configurable free-tier LLM provider for interpretation when needed.

### Tests Required

- Deterministic readiness score tests.
- AI schema validation tests.
- Evidence citation tests.
- Non-technical profile tests.

### Definition Of Done

- Dashboard summarizes MVP analyses.
- Specialization includes confidence and evidence.
- Non-technical and technical profiles both receive relevant output.

## Milestone 11: MVP Basic Report

### Objective

Generate a downloadable career report using existing MVP analyses.

### Features Included

- Candidate summary.
- Detected specializations.
- Confidence scores.
- Career-readiness scores.
- Resume findings.
- ATS analysis.
- Strengths.
- Weaknesses.
- Skill gaps.

### Files Or Modules Likely To Be Created

- `backend/app/reports/report_builder.py`.
- `backend/app/api/routes/reports.py`.
- `frontend/src/features/reports/`.

### Dependencies

- Milestone 10.

### Tests Required

- Report assembly tests.
- Download authorization tests.
- Report content snapshot tests.

### Definition Of Done

- User can generate and download a basic report.
- Report includes only available MVP sections.
- Report generation is cached by profile and analysis versions.

## Milestone 12: Privacy Baseline And MVP Hardening

### Objective

Complete the MVP privacy baseline and make the MVP deployable.

### Features Included

- Private document storage.
- User-specific access control.
- No sensitive document contents in logs.
- Clear data retention display.
- Initial delete-profile flow.
- Deployment configuration.

### Files Or Modules Likely To Be Created

- `backend/app/privacy/`.
- `backend/app/api/routes/privacy.py`.
- `frontend/src/features/privacy/`.
- `render.yaml`.
- `vercel.json`.

### Dependencies

- Milestone 11.

### Tests Required

- Access-control tests.
- Deletion tests.
- Log-safety review.
- Frontend production build.
- Backend deployment smoke test.

### Definition Of Done

- MVP can be deployed on free-tier services.
- Privacy baseline is functional.
- Core user journey works end to end.

## Milestone 13: Optional GitHub Analysis

### Objective

Add public GitHub profile analysis for technical candidates without making it required.

### Features Included

- Public repositories.
- Languages.
- Frameworks.
- README quality.
- Testing practices.
- Project complexity.
- CI/CD and Docker signals.
- Recent activity.
- Open-source contributions.

### Files Or Modules Likely To Be Created

- `backend/app/integrations/github.py`.
- `backend/app/analysis/github_profile.py`.
- `frontend/src/features/sources/github-source.tsx`.

### Dependencies

- MVP.

### Tests Required

- GitHub API client tests with mocks.
- Public profile parsing tests.
- Optional-source profile update tests.

### Definition Of Done

- Technical users can add GitHub.
- Non-technical users are not penalized for missing GitHub.
- Stars are supporting signals only.

## Milestone 14: Portfolio And LinkedIn Inputs

### Objective

Add optional portfolio and LinkedIn profile analysis without scraping LinkedIn directly.

### Features Included

- Portfolio URL extraction.
- Technical and non-technical portfolio analysis.
- LinkedIn PDF, export, or pasted-content input.
- LinkedIn profile analysis.

### Files Or Modules Likely To Be Created

- `backend/app/integrations/portfolio.py`.
- `backend/app/parsing/linkedin_parser.py`.
- `backend/app/analysis/portfolio.py`.
- `backend/app/analysis/linkedin.py`.
- `frontend/src/features/sources/portfolio-source.tsx`.
- `frontend/src/features/sources/linkedin-source.tsx`.

### Dependencies

- Milestone 13.

### Tests Required

- Portfolio extraction tests with fixtures.
- LinkedIn pasted/PDF fixture tests.
- No LinkedIn scraping test or policy check.
- Non-technical portfolio analysis tests.

### Definition Of Done

- Users can add optional portfolio and LinkedIn data.
- Direct LinkedIn scraping is not implemented.
- Profile evidence updates from optional sources.

## Milestone 15: Resume And LinkedIn Optimization

### Objective

Generate on-demand profile optimization outputs from verified evidence.

### Features Included

- Resume bullet rewriting.
- Professional summary optimization.
- LinkedIn headline.
- LinkedIn About.
- LinkedIn experience descriptions.
- Suggested skills and featured projects.
- Certification and keyword recommendations.

### Files Or Modules Likely To Be Created

- `backend/app/ai/resume_improvement.py`.
- `backend/app/ai/linkedin_optimization.py`.
- `backend/app/cache/output_cache.py`.
- `frontend/src/features/generation/`.

### Dependencies

- Milestone 14.

### Tests Required

- Structured output schema tests.
- No-fabrication prompt tests.
- Missing metric handling tests.
- Cache reuse tests.

### Definition Of Done

- Users generate only requested sections.
- Outputs cite profile evidence where applicable.
- Missing facts are requested or omitted, not invented.

## Milestone 16: Cover Letters And Resume Tailoring

### Objective

Generate job-specific application material recommendations.

### Features Included

- Cover letter generation.
- Email application version.
- Job-specific resume tailoring.
- Keywords to add.
- Bullets to reorder.
- Projects to highlight.

### Files Or Modules Likely To Be Created

- `backend/app/ai/cover_letters.py`.
- `backend/app/ai/resume_tailoring.py`.
- `frontend/src/features/jobs/application-materials.tsx`.

### Dependencies

- Milestone 15.

### Tests Required

- Job-specific context tests.
- No-fabrication tests.
- Cache-key tests using job description hash.

### Definition Of Done

- Outputs are generated on demand.
- Outputs are tied to a selected target job.
- Outputs preserve factual accuracy.

## Milestone 17: Projects, Roadmaps, And Learning Plans

### Objective

Recommend skill-building actions for technical and non-technical users.

### Features Included

- Personalized project recommendations.
- Career roadmap.
- Daily, weekly, and monthly learning plans.
- 7-day, 30-day, 90-day, and six-month durations.

### Files Or Modules Likely To Be Created

- `backend/app/ai/project_recommendations.py`.
- `backend/app/ai/roadmaps.py`.
- `backend/app/ai/learning_plans.py`.
- `frontend/src/features/roadmap/`.

### Dependencies

- Milestone 16.

### Tests Required

- Structured output tests.
- Profession-specific recommendation tests.
- RAG citation tests when references are used.
- Cache tests.

### Definition Of Done

- Users receive realistic, profile-specific plans.
- Recommendations map to skill gaps.
- Technical and non-technical examples are supported.

## Milestone 18: Saved History And Cache Management

### Objective

Expose saved analysis and generated-output history with cache invalidation.

### Features Included

- Saved candidate profiles.
- Resume analyses.
- Skill-gap reports.
- Roadmaps.
- Cover letters.
- LinkedIn rewrites.
- Generated reports.
- Cache status.

### Files Or Modules Likely To Be Created

- `backend/app/history/`.
- `backend/app/cache/`.
- `frontend/src/features/history/`.

### Dependencies

- Milestone 17.

### Tests Required

- Cache hit tests.
- Cache invalidation tests.
- History authorization tests.
- Profile version invalidation tests.

### Definition Of Done

- Users can reopen generated outputs.
- Expensive outputs are not regenerated unnecessarily.
- Profile updates invalidate relevant outputs.

## Milestone 19: RAG Foundation And Job Retrieval

### Objective

Add RAG infrastructure for job descriptions, role frameworks, and career guidance.

### Features Included

- RAG document ingestion.
- pgvector chunks.
- Semantic retrieval.
- Role and job reference lookup.
- Retrieved job listings or internal job dataset support.

### Files Or Modules Likely To Be Created

- `backend/app/rag/ingestion.py`.
- `backend/app/rag/retrieval.py`.
- `backend/app/jobs/retrieval.py`.
- `supabase/migrations/*_rag.sql`.

### Dependencies

- Phase 2 complete.

### Tests Required

- Chunking tests.
- Embedding storage tests with mocks if needed.
- Retrieval relevance tests.
- Source citation tests.

### Definition Of Done

- RAG chunks can be ingested and queried.
- Retrieved chunks include source metadata.
- AI features can consume retrieved references.

## Milestone 20: Job Matching And Explainable Recommendations

### Objective

Retrieve, rank, and explain relevant jobs using structured filtering, semantic retrieval, and RAG.

### Features Included

- Job matching.
- Explainable job recommendations.
- Match score.
- Matched and missing skills.
- Relevant experience.
- Potential concerns.
- Apply recommendation.

### Files Or Modules Likely To Be Created

- `backend/app/matching/job_matcher.py`.
- `backend/app/ai/job_recommendations.py`.
- `frontend/src/features/jobs/job-matches.tsx`.

### Dependencies

- Milestone 19.

### Tests Required

- Filtering tests.
- Ranking tests.
- Explanation schema tests.
- Evidence consistency tests.

### Definition Of Done

- User receives ranked job matches.
- Each match includes explainable evidence.
- Deterministic ranking is used before AI explanation.

## Milestone 21: Interview Preparation And Claim Questions

### Objective

Generate personalized interview preparation materials.

### Features Included

- Technical or role-specific questions.
- Behavioral questions.
- Situational questions.
- Resume-based questions.
- Project-based questions.
- Portfolio-based questions.
- Leadership questions.
- Career-transition questions.
- Job-specific questions.
- Resume claim verification questions.

### Files Or Modules Likely To Be Created

- `backend/app/ai/interview_questions.py`.
- `backend/app/ai/claim_verification.py`.
- `frontend/src/features/interview/prep.tsx`.

### Dependencies

- Milestone 20.

### Tests Required

- Question category tests.
- Evidence reference tests.
- No lie-detector wording test.

### Definition Of Done

- Interview prep is personalized.
- Claim questions use evidence strength language.
- The system does not claim to detect lies.

## Milestone 22: Mock Interview And Answer Evaluation

### Objective

Support conversational mock interviews and standalone answer evaluation.

### Features Included

- Mock interview sessions.
- Follow-up questions.
- Answer evaluation.
- STAR method feedback.
- Relevance, clarity, evidence, depth, and confidence feedback.

### Files Or Modules Likely To Be Created

- `backend/app/interview/sessions.py`.
- `backend/app/ai/mock_interview.py`.
- `backend/app/ai/answer_evaluation.py`.
- `frontend/src/features/interview/session.tsx`.

### Dependencies

- Milestone 21.

### Tests Required

- Session state tests.
- Answer evaluation schema tests.
- Follow-up generation tests.
- No-fabrication tests.

### Definition Of Done

- User can complete a short mock interview flow.
- Feedback is structured and actionable.
- Improved answers do not invent experience.

## Milestone 23: Recruiter Outreach And Career Transition

### Objective

Add advanced career communication and transition support.

### Features Included

- LinkedIn connection message.
- Recruiter outreach message.
- Job-application email.
- Follow-up email.
- Interview thank-you email.
- Referral request.
- Short professional introduction.
- Career transition analysis.

### Files Or Modules Likely To Be Created

- `backend/app/ai/outreach.py`.
- `backend/app/ai/career_transition.py`.
- `frontend/src/features/outreach/`.
- `frontend/src/features/transition/`.

### Dependencies

- Milestone 22.

### Tests Required

- Message format tests.
- Career-transition recommendation tests.
- Evidence-only generation tests.

### Definition Of Done

- Outreach content uses existing candidate profile.
- Transition analysis identifies transferable skills and realistic next steps.

## Milestone 24: Advanced Reports, Privacy, And Production Hardening

### Objective

Complete final product scope and harden for production use.

### Features Included

- Full downloadable career report.
- Interview questions in report.
- LinkedIn recommendations in report.
- Job matches in report.
- Advanced privacy controls.
- Optional deletion after parsing.
- Delete-my-data control.
- User data summary.

### Files Or Modules Likely To Be Created

- `backend/app/reports/full_report_builder.py`.
- `backend/app/privacy/deletion.py`.
- `frontend/src/features/privacy/data-controls.tsx`.
- `frontend/src/features/reports/full-report.tsx`.

### Dependencies

- Milestone 23.

### Tests Required

- Full report tests.
- Data deletion tests.
- Storage deletion tests.
- Access-control regression tests.
- Production smoke tests.

### Definition Of Done

- Complete long-term feature scope is implemented.
- Privacy controls are complete.
- Final report includes all available sections.
- Product is deployable on approved free-tier stack.
