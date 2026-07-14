# AI Career Intelligence Platform

## Project Role

This repository is for an AI Career Intelligence Platform that helps candidates analyze their professional profile, compare it against target roles, improve application materials, prepare for interviews, and build a career roadmap.

The complete feature-list PDF is the long-term product scope. Features may be phased, but they must not be removed from the final product scope without an explicit product decision recorded in `docs/DECISIONS.md`.

## Non-Negotiable Product Rules

- Resume input is required for every candidate profile.
- GitHub, LinkedIn, and portfolio inputs are optional.
- The product must support technical and non-technical professions.
- Do not assume every user has GitHub, a technical portfolio, programming experience, a computer-science degree, or LinkedIn.
- Do not implement direct LinkedIn scraping. Accept LinkedIn PDF exports, pasted profile content, or exported user data only.
- Do not fabricate achievements, metrics, skills, education, certifications, projects, or work experience.
- Do not describe the system as a lie detector. Use evidence strength, consistency checks, and clarification prompts instead.
- Avoid repeatedly sending full resumes or raw documents to an AI model.
- Reuse one normalized candidate profile across all features.
- Prefer deterministic Python logic for parsing, validation, ATS scoring, skill comparison, filtering, and ranking.
- Use AI only where interpretation, rewriting, explanations, interview interactions, or personalized recommendations are needed.
- Generate expensive optional outputs only when requested and cache them.
- Keep the system buildable and deployable on free-tier services.
- Do not introduce paid-only tools or services.

## Approved Stack

Frontend:

- React
- Vite
- TypeScript
- Tailwind CSS
- shadcn/ui
- TanStack Query
- React Hook Form
- Zod

Backend:

- Python
- FastAPI
- Pydantic
- PyMuPDF
- python-docx
- HTTPX
- BeautifulSoup or Trafilatura

AI:

- OpenAI Agents SDK where orchestration is genuinely useful
- Configurable free-tier LLM provider
- Structured Pydantic outputs
- RAG for job descriptions, role frameworks, and career guidance

Data:

- Supabase PostgreSQL
- Supabase Auth
- Supabase Storage
- pgvector

Deployment:

- Vercel for frontend
- Render for backend
- Supabase for persistent data
- GitHub Actions for CI/CD

## Documentation Map

- `docs/PROJECT_SPEC.md`: product vision, users, journeys, phases, constraints.
- `docs/FEATURES.md`: full long-term feature scope and phase allocation.
- `docs/ARCHITECTURE.md`: system architecture, services, agents, RAG, caching, privacy.
- `docs/DATA_MODELS.md`: normalized candidate profile and database entities.
- `docs/API_SPEC.md`: initial API surface and endpoint responsibilities.
- `docs/DEVELOPMENT_PLAN.md`: sequential milestones with acceptance criteria.
- `docs/DECISIONS.md`: architectural decisions and reasons.
- `docs/LOCAL_DEVELOPMENT.md`: local install, run, and verification commands.
- `docs/PRODUCTION_SMOKE_TEST.md`: production smoke-test checklist and automation.
- `docs/OPERATIONS.md`: production operations, troubleshooting, rate-limit tuning, and support runbook.
- `docs/LAUNCH_READINESS.md`: current launch-readiness status, blockers, risks, and next work.

## Development Guidance

- Start with Milestone 1 only after explicit user approval.
- Keep each milestone independently testable.
- Add tests with every meaningful behavior change.
- Keep AI prompts and structured output schemas versioned.
- Keep deterministic scoring rules explainable and inspectable.
- Store raw uploaded documents privately and minimize their reuse after parsing.
- Store parsed profile facts, evidence references, and derived outputs separately.
- Cache AI outputs by input hash, profile version, target job version, prompt version, and model/provider.
