# Architecture

## Overview

The platform uses a React frontend, FastAPI backend, Supabase data services, deterministic Python services, optional AI services, and RAG for reference-backed job and career guidance.

The central architectural rule is that raw documents are parsed once into structured facts and evidence references. Features reuse the normalized candidate profile instead of repeatedly sending full resumes or raw documents to AI providers.

## System Components

### Frontend

Stack:

- React.
- Vite.
- TypeScript.
- Tailwind CSS.
- shadcn/ui.
- TanStack Query.
- React Hook Form.
- Zod.

Responsibilities:

- Authentication flows via Supabase Auth.
- Resume upload and optional source submission.
- Career goal and target role forms.
- Analysis dashboard.
- Job description submission.
- Report preview and download.
- On-demand generation controls.
- Saved history views.

### Backend API

Stack:

- Python.
- FastAPI.
- Pydantic.

Responsibilities:

- Authenticated API boundary.
- File upload coordination with Supabase Storage.
- Resume parsing orchestration.
- Candidate profile normalization.
- Deterministic scoring and matching.
- AI orchestration only where needed.
- RAG retrieval.
- Caching and output versioning.
- PDF report generation.

### Supabase

Responsibilities:

- PostgreSQL database.
- Auth.
- Private document storage.
- Row-level security.
- pgvector embeddings for RAG and semantic matching.

### Deployment

- Frontend: Vercel.
- Backend: Render.
- Data and storage: Supabase.
- CI/CD: GitHub Actions.

The project must remain compatible with free-tier limits. Heavy or optional tasks should be user-triggered and cached.

## Data Flow

### Profile Creation

1. User uploads resume.
2. Backend stores file privately in Supabase Storage.
3. Backend parses PDF with PyMuPDF or DOCX with python-docx.
4. Parser extracts text, sections, dates, contact info, skills, projects, education, certifications, and work experience.
5. Deterministic validators flag missing sections, date issues, formatting concerns, and weak resume signals.
6. AI may be used to interpret ambiguous role, specialization, seniority, and evidence only from extracted structured text.
7. Backend writes one normalized candidate profile with source-tagged evidence.

### Job Comparison

1. User pastes or uploads a target job description.
2. Backend extracts structured requirements using deterministic rules and limited AI when needed.
3. Deterministic services compare profile skills, experience, seniority, education, tools, and keywords against the job.
4. Backend computes skill-gap and ATS-readiness outputs.
5. AI may explain gaps and recommended next steps using structured profile and comparison summaries.

### Optional Generation

1. User requests a specific expensive output.
2. Backend computes an input hash from profile version, selected job, prompt version, output type, and model/provider.
3. Backend returns cached output if available.
4. If not cached, backend calls AI with minimal structured context and stores the output.

## Deterministic Services

Use deterministic Python logic whenever possible:

- Resume text extraction.
- DOCX extraction.
- Section detection.
- Contact information detection.
- Date consistency checks.
- Keyword extraction and normalization.
- Skill taxonomy matching.
- Job requirement parsing where reliable.
- ATS-readiness scoring.
- Skill comparison.
- Profile completeness scoring.
- Structured filtering and ranking.
- Cache-key generation.
- Report assembly.

These services should be testable without AI calls.

## AI Services

Use AI only for:

- Ambiguous profile interpretation.
- Specialization and seniority reasoning.
- Rewriting resume bullets and summaries.
- Explanation generation.
- Personalized project recommendations.
- Roadmap and learning-plan generation.
- Cover letters.
- LinkedIn rewrites.
- Interview question generation.
- Mock interview dialogue.
- Answer evaluation.
- Recruiter outreach content.
- Career transition recommendations.

AI requests must use structured Pydantic input and output schemas. Prompts must instruct the model not to fabricate facts and to ask for missing metrics or omit them.

## Agent Responsibilities

Use the OpenAI Agents SDK only where orchestration adds value. Simple deterministic tasks should remain plain services.

Potential agents:

- Profile Interpretation Agent: interprets normalized evidence into specialization, seniority, and confidence.
- Resume Improvement Agent: rewrites bullets and summaries without inventing facts.
- Recommendation Agent: generates projects, roadmaps, learning plans, and next steps.
- Interview Agent: conducts mock interviews and evaluates answers.
- Career Transition Agent: maps transferable skills and transition paths.
- Report Agent: summarizes existing outputs into user-facing report sections.

Agents must consume structured candidate-profile summaries, evidence references, and relevant job summaries, not raw full documents.

## RAG Workflow

RAG is used for:

- Job descriptions.
- Role frameworks.
- Skill taxonomies.
- Career guidance.
- Interview question banks.
- Project recommendation patterns.

Workflow:

1. Ingest approved reference documents or job records.
2. Chunk text into source-attributed units.
3. Store embeddings in Supabase pgvector.
4. Retrieve top relevant chunks by query, role, specialization, seniority, and career goal.
5. Rerank deterministically where possible.
6. Send only relevant chunks plus structured profile context to AI.
7. Store citations or source references with generated recommendations.

## Caching Strategy

Cache optional expensive outputs:

- LinkedIn rewrites.
- Resume bullet rewrites.
- Professional summaries.
- Cover letters.
- Resume tailoring.
- Project recommendations.
- Roadmaps.
- Learning plans.
- Interview questions.
- Mock interview evaluations.
- Recruiter outreach messages.
- Reports.

Cache key inputs:

- User ID.
- Candidate profile ID and version.
- Source versions.
- Target job ID or job description hash.
- Output type.
- Prompt version.
- Model provider and model ID.
- RAG source version, when applicable.

Invalidate caches when relevant profile facts, source documents, job descriptions, prompt versions, or scoring rules change.

## Privacy And Security

Requirements:

- Store uploaded documents privately.
- Enforce user-specific access control with Supabase RLS.
- Never expose uploaded resumes publicly.
- Do not log raw resume text, LinkedIn text, or sensitive document contents.
- Allow optional deletion after parsing.
- Provide delete-my-data workflow.
- Track what data is retained.
- Keep provider calls minimal and structured.
- Expose only non-secret provider configuration health so external LLM setup can validate supported provider names, required model settings, API key presence, placeholder key values, and base URL format without revealing API key values or making paid network calls.
- Avoid direct LinkedIn scraping.
- Avoid unsupported claims about commercial ATS systems.

## Production Diagnostics

- Add `X-Request-ID` to every backend response so frontend reports, Render logs, and API traces can be correlated without paid observability tooling.
- Preserve a caller-provided `X-Request-ID` when it is present and reasonably sized; otherwise generate a UUID-based value.
- Add `X-Process-Time-ms` to backend responses for lightweight latency checks during smoke testing.
- Do not include raw resume text, uploaded document content, API keys, or JWTs in diagnostic headers or logs.

## Usage Analytics

- Usage analytics are anonymous, aggregate product events stored in Supabase through the backend service role.
- Events do not store `user_id`, `profile_id`, email, source URLs, resume text, job text, generated AI output, uploaded document content, API keys, or JWTs.
- The frontend creates a random session-scoped identifier in `sessionStorage`; this identifier is not tied to Supabase Auth.
- Backend validation accepts only compact event names, surface names, paths without query strings, and primitive metadata values.
- Backend sanitization drops sensitive metadata keys and unsupported nested values before storage.
- Analytics calls are fire-and-forget from the frontend so they never block the user workflow.

## Testing Strategy

Backend tests:

- Parser tests for PDF and DOCX fixtures.
- Section detection tests.
- Date and contact validation tests.
- Skill normalization tests.
- ATS scoring rule tests.
- Job description extraction tests.
- Skill-gap comparison tests.
- Cache-key tests.
- API contract tests.
- RLS and access-control integration tests where feasible.

Frontend tests:

- Form validation tests.
- Upload flow tests.
- Dashboard rendering tests.
- On-demand generation state tests.
- Error and empty-state tests.

AI tests:

- Schema validation.
- Prompt regression snapshots.
- Fabrication guard tests.
- Missing-metric behavior tests.
- Cached-output reuse tests.

Deployment tests:

- Build frontend.
- Run backend tests.
- Verify environment variables.
- Verify database migrations.
- Verify health endpoint.

## Free-Tier Constraints

- Prefer asynchronous or user-triggered heavy tasks.
- Avoid unnecessary AI calls.
- Cache aggressively.
- Store parsed summaries and evidence references.
- Keep files in Supabase Storage with lifecycle controls.
- Keep backend stateless where possible for Render compatibility.
- Design local development to run without paid services by using mock providers where needed.
