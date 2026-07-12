# Project Spec

## Product Vision

The AI Career Intelligence Platform helps candidates understand where they stand, what roles fit them, what gaps matter, and what concrete actions will improve their job-market competitiveness.

The product combines a required resume with optional GitHub, LinkedIn, portfolio, job description, career goal, and target-role inputs. It converts those sources into one normalized candidate profile that every analysis, recommendation, and generated output reuses.

The long-term product scope is the complete feature-list PDF. Implementation is prioritized into MVP, Phase 2, and Phase 3, but no listed feature is removed from the final product.

## Target Users

- Students and early-career candidates looking for a first job or internship.
- Professionals improving an existing profile.
- Candidates switching careers or specializations.
- Candidates preparing for a target role.
- Senior candidates moving toward leadership or management.
- Technical candidates, including software, data, AI, DevOps, QA, and cybersecurity roles.
- Non-technical candidates, including marketing, sales, HR, recruitment, finance, accounting, banking, operations, customer service, content, design, and supply chain roles.

## Core Principles

- Resume is mandatory; all other sources are optional.
- Candidate evaluation must adapt to the candidate's field.
- The platform must not penalize candidates for missing GitHub, LinkedIn, or a technical portfolio.
- One normalized candidate profile is the reusable source of truth.
- Deterministic logic handles parsing, validation, matching, scoring, filtering, ranking, and most comparisons where possible.
- AI handles interpretation, rewriting, explanations, interview conversations, and personalized recommendations.
- AI outputs must cite profile evidence and must not invent missing facts.
- Expensive optional outputs are generated only on demand and cached.
- The product must remain practical on free-tier infrastructure.

## Product Scope

The final product includes:

- Multi-source candidate profile analysis.
- Career goal selection.
- Specialization detection.
- Career readiness dashboard.
- Resume analysis.
- ATS readiness scoring.
- Resume bullet rewriting.
- Professional summary optimization.
- GitHub profile analysis.
- Portfolio analysis.
- LinkedIn profile analysis.
- LinkedIn profile optimization.
- Target job description analysis.
- Skill gap analysis.
- Job matching.
- Explainable job recommendations.
- Personalized project recommendations.
- Personalized career roadmap.
- Daily, weekly, and monthly learning plans.
- Interview preparation.
- Interactive mock interview.
- Resume claim verification questions.
- Answer evaluation.
- Cover letter generation.
- Job-specific resume tailoring.
- Recruiter outreach content.
- Career transition analysis.
- Evidence-based recommendations.
- Universal profession support.
- Downloadable career report.
- Saved analysis history.
- Privacy and data controls.

## Phase Boundaries

### MVP

The MVP proves the core platform loop:

1. Upload a resume.
2. Create a normalized candidate profile.
3. Select a career goal and target role.
4. Analyze resume quality and ATS readiness.
5. Parse or paste a target job description.
6. Compare profile against the target role.
7. Show skill gaps and explainable recommendations.
8. Generate a basic career readiness dashboard.
9. Generate a basic downloadable career report.

MVP focuses on deterministic processing first and limited AI usage for structured interpretation and explanations.

### Phase 2

Phase 2 expands evidence sources and application-material generation:

1. Optional GitHub analysis.
2. Optional portfolio analysis.
3. Optional LinkedIn PDF, export, or pasted-content analysis.
4. LinkedIn profile optimization.
5. Resume bullet rewriting.
6. Professional summary optimization.
7. Cover letter generation.
8. Job-specific resume tailoring.
9. Personalized project recommendations.
10. Personalized roadmap and learning plans.
11. Saved analysis history and stronger caching.

### Phase 3

Phase 3 adds advanced, interactive, and retrieval-heavy features:

1. Job retrieval and RAG-based matching.
2. Explainable job recommendations at scale.
3. Interview preparation.
4. Interactive mock interviews.
5. Answer evaluation.
6. Resume claim verification questions.
7. Recruiter outreach content.
8. Career transition analysis.
9. Advanced privacy controls.
10. More complete downloadable reports.

## Main User Journeys

### Core MVP Journey

1. User creates an account.
2. User uploads a resume.
3. System parses the resume into structured facts and evidence references.
4. User selects career goal, target role, location preference, and experience context.
5. System builds a normalized candidate profile.
6. User pastes or uploads a target job description.
7. System extracts deterministic job requirements and keywords.
8. System calculates resume, ATS, skill alignment, and readiness scores.
9. System explains strengths, weaknesses, gaps, and recommended next steps.
10. User downloads a basic report.

### Expanded Profile Journey

1. User adds optional GitHub, portfolio, and LinkedIn content.
2. System parses and validates each source.
3. System updates the candidate profile with source-tagged evidence.
4. System recalculates profile completeness and relevant scores.
5. User requests optional generated outputs such as LinkedIn rewrite, resume bullets, cover letter, or projects.

### Interview Preparation Journey

1. User selects a target role or job.
2. System generates personalized interview questions from profile evidence and job requirements.
3. User answers questions.
4. System evaluates answers for relevance, clarity, specificity, consistency, and structure.
5. System asks follow-ups and suggests improvements.

### Career Transition Journey

1. User selects a target specialization different from current evidence.
2. System identifies transferable skills and missing foundational knowledge.
3. System recommends realistic transitional roles, projects, learning sequence, resume positioning, and likely interview concerns.

## Success Criteria

- A user can complete the MVP journey without providing GitHub, LinkedIn, or portfolio inputs.
- A non-technical user receives relevant evaluation criteria rather than developer-focused feedback.
- A technical user can optionally benefit from GitHub and portfolio analysis.
- AI outputs are traceable to stored candidate-profile evidence.
- Expensive AI generations are cached and reused when inputs have not changed.
- The app can deploy to Vercel, Render, and Supabase free tiers.
- The system avoids direct LinkedIn scraping and avoids unsupported claims about commercial ATS scores.
