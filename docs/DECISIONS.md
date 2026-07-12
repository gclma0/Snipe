# Decisions

## ADR-001: Preserve PDF Feature List As Long-Term Scope

Decision: The complete feature-list PDF is accepted as the long-term product scope.

Reason: The user explicitly approved the feature list and requested prioritization without removing final product features.

Implications:

- Features can move between phases, but removal requires a recorded decision.
- Documentation and implementation plans must track all 32 feature areas.

## ADR-002: Use Three Implementation Phases

Decision: Divide implementation into MVP, Phase 2, and Phase 3.

Reason: The full product is too large for an initial build. Phasing creates a usable product early while preserving the complete final scope.

Implications:

- MVP proves the core resume-to-profile-to-analysis loop.
- Phase 2 adds optional sources and generated application materials.
- Phase 3 adds advanced matching, interviews, outreach, transition support, and advanced privacy.

## ADR-003: Resume Required, Other Sources Optional

Decision: A resume is required. GitHub, LinkedIn, and portfolio inputs are optional.

Reason: The resume is the minimum reliable source for a career profile. Optional sources enrich the profile but must not block non-technical users.

Implications:

- The product must work fully for users without GitHub, LinkedIn, or portfolio inputs.
- Scores must account for applicability by profession.

## ADR-004: One Normalized Candidate Profile

Decision: All features reuse one normalized candidate profile.

Reason: Reusing a structured profile avoids repeated raw-document AI calls, reduces cost, improves consistency, and supports caching.

Implications:

- Raw documents are parsed into facts and evidence.
- AI receives minimal structured context.
- Profile versioning becomes central to cache invalidation.

## ADR-005: Deterministic Logic First

Decision: Use deterministic Python logic for parsing, validation, ATS scoring, skill comparison, filtering, and ranking whenever possible.

Reason: Deterministic services are cheaper, testable, explainable, and more reliable for rule-based tasks.

Implications:

- AI is reserved for interpretation, rewriting, explanations, interactive interviews, and personalized recommendations.
- Scoring rules should be versioned and tested.

## ADR-006: AI Must Not Fabricate Candidate Facts

Decision: AI outputs must not invent achievements, metrics, skills, education, certifications, projects, or experience.

Reason: Fabricated career information can harm users and undermine trust.

Implications:

- Prompts must include no-fabrication rules.
- Missing metrics should trigger questions, placeholders, or metric-free rewrites.
- Generated outputs should reference candidate evidence where applicable.

## ADR-007: No Direct LinkedIn Scraping

Decision: The system accepts LinkedIn PDFs, exported data, or pasted content, but does not scrape LinkedIn directly.

Reason: Direct scraping can violate platform terms and create reliability and compliance risks.

Implications:

- LinkedIn features must use user-provided content.
- API and UI language must make this clear.

## ADR-008: Do Not Describe Claim Checks As Lie Detection

Decision: The system does not claim to detect lies.

Reason: Resume claim analysis can surface evidence strength and inconsistencies, but it cannot reliably determine intent or truthfulness.

Implications:

- Use terms such as evidence strength, clarification needed, consistency, and interview verification questions.
- Add tests or content checks to prevent lie-detector wording.

## ADR-009: On-Demand Generation And Caching

Decision: Expensive optional outputs are generated only when requested and cached by input hash, profile version, job version, prompt version, provider, and model.

Reason: Free-tier deployment requires tight control of compute and AI costs.

Implications:

- UI should expose explicit generate buttons.
- Backend should return cached outputs when inputs have not changed.
- Cache invalidation must be version-aware.

## ADR-010: Approved Free-Tier Stack

Decision: Use React, Vite, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query, React Hook Form, Zod, FastAPI, Pydantic, Supabase, pgvector, Vercel, Render, and GitHub Actions.

Reason: The stack matches the user's approved plan and can be deployed with free-tier services.

Implications:

- Do not introduce paid-only dependencies or hosted services.
- Any provider-specific AI integration must remain configurable.

## ADR-011: RAG For Reference-Backed Guidance

Decision: Use RAG for job descriptions, role frameworks, and career guidance.

Reason: RAG keeps recommendations grounded in retrievable references and supports evolving job and skill data.

Implications:

- Store chunks and embeddings in Supabase pgvector.
- Generated recommendations should cite or record source references where applicable.

## ADR-012: Support Technical And Non-Technical Professions Equally

Decision: Evaluation logic must adapt to profession and not default to software-engineering assumptions.

Reason: The product scope includes marketing, finance, HR, sales, design, banking, operations, customer service, content, and other non-technical users.

Implications:

- Skill taxonomies and scoring rules need profession tags.
- Portfolio and project recommendations must support non-technical evidence.
- GitHub and technical portfolio absence must not reduce scores when irrelevant.
