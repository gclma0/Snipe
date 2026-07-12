# Features

## Scope Rule

This file preserves the complete long-term feature scope from the approved feature-list PDF. Features are prioritized by phase, but all remain part of the final product unless a later product decision explicitly changes scope.

## MVP Features

### 1. Multi-Source Candidate Profile Analysis

MVP includes resume upload as the required source and supports career goal, preferred role, and target job description inputs. The architecture must already allow optional GitHub, LinkedIn, and portfolio sources to be added later.

The system creates one reusable, structured candidate profile.

### 2. Career Goal Selection

Users can select goals such as:

- Find a first job.
- Find an internship.
- Improve current professional profile.
- Switch careers.
- Transition into a specialization.
- Prepare for a target role.
- Move into a senior position.
- Move into leadership or management.
- Improve job-market competitiveness.

All recommendations use the selected goal.

### 3. Specialization Detection

The system identifies current and target specialization based on evidence from the profile.

Supported examples include:

- Backend Development.
- Frontend Development.
- Full-Stack Development.
- QA Automation.
- Manual QA.
- Data Analysis.
- Data Science.
- AI and Machine Learning.
- DevOps.
- Cybersecurity.
- Product Management.
- Project Management.
- UI/UX Design.
- Digital Marketing.
- Sales.
- Human Resources.
- Recruitment.
- Finance.
- Accounting.
- Banking.
- Operations.
- Customer Service.
- Content Writing.
- Graphic Design.
- Supply Chain.

The result includes primary specialization, secondary specializations, estimated seniority, confidence scores, and evidence.

### 4. Career Readiness Dashboard

MVP includes:

- Overall career-readiness score.
- Resume-quality score.
- ATS-readiness score.
- Skill-alignment score.
- Profile-completeness score.

Later phases add job-match, interview-readiness, and portfolio-strength scores.

Every score must include an explanation.

### 5. Resume Analysis

The system evaluates:

- Resume structure.
- Section completeness.
- Contact-information placement.
- Professional summary.
- Work-experience descriptions.
- Project descriptions.
- Education.
- Skills.
- Certifications.
- Grammar and clarity.
- Repetitive wording.
- Weak action verbs.
- Overly long bullets.
- Missing achievements.
- Missing measurable impact.
- Date inconsistencies.
- Role relevance.
- Formatting and readability concerns.

Corrections are prioritized by importance.

### 6. ATS Readiness Score

The platform calculates its own explainable ATS-readiness score using deterministic rules and job-specific comparison.

The score can consider:

- Required resume sections.
- Contact details.
- Relevant keywords.
- Required skills.
- Experience relevance.
- Job-title alignment.
- Bullet-point quality.
- Quantified achievements.
- Formatting and readability.
- Job-description compatibility.

The product must never present this as a guaranteed score from every commercial ATS.

### 13. Target Job Description Analysis

Users can paste or upload a job description in MVP. Later phases may support internal datasets and retrieved listings.

The system extracts:

- Required skills.
- Preferred skills.
- Responsibilities.
- Experience requirements.
- Education requirements.
- Tools and technologies.
- Soft skills.
- Seniority expectations.
- Important ATS keywords.

### 14. Skill Gap Analysis

The platform compares the candidate profile against a target job or career path.

Skills are categorized as:

- Matched.
- Partially matched.
- Missing.
- Transferable.
- Claimed but unverified.
- Not relevant.

For important gaps, the system explains why the skill matters, urgency, development path, demonstrable project or task, and whether it is essential or optional.

### 28. Evidence-Based Recommendations

Every major conclusion must show supporting evidence. This applies to specializations, skill scores, ATS feedback, job matches, project recommendations, interview questions, and roadmap priorities.

### 29. Universal Profession Support

The product supports multiple professions and must not assume every user has technical artifacts. Evaluation changes according to the candidate's field.

Examples:

- Developers can be evaluated through code and repositories.
- Designers can be evaluated through case studies.
- Marketers can be evaluated through campaigns and analytics.
- Sales professionals can be evaluated through targets and conversions.
- HR professionals can be evaluated through hiring, retention, and HR operations.
- Finance professionals can be evaluated through analysis, reporting, controls, and business impact.

### 30. Downloadable Career Report

MVP includes a basic downloadable report with candidate summary, detected specializations, readiness scores, resume findings, ATS analysis, strengths, weaknesses, and skill gaps.

Later phases add job matches, recommended projects, career roadmap, interview questions, and LinkedIn recommendations.

### 32. Privacy and Data Controls

MVP includes private document storage, user-specific access control, no public resume access, no sensitive document contents in logs, and clear retention notices.

## Phase 2 Features

### 7. Resume Bullet Rewriting

AI rewrites weak resume bullets into stronger, action-oriented statements. It can improve clarity, tone, detail, achievement focus, relevance, keywords, and conciseness.

The system must not invent achievements or numerical results. When metrics are unavailable, it can ask for the missing value, suggest a placeholder, or rewrite without fabricated numbers.

### 8. Professional Summary Optimization

The system creates or improves resume summaries, career objectives, short biographies, and role-specific profile summaries using verified candidate-profile facts only.

### 9. GitHub Profile Analysis

For technical candidates, the system can analyze public GitHub information:

- Public repositories.
- Programming languages.
- Frameworks.
- Repository topics.
- README quality.
- Documentation.
- Testing practices.
- Project complexity.
- Code organization.
- Dependency files.
- CI/CD workflows.
- Docker usage.
- Recent activity.
- Project diversity.
- Open-source contributions.

Popularity metrics such as stars are supporting signals, not primary skill measures.

### 10. Portfolio Analysis

The platform evaluates technical and non-technical portfolios:

- Project quality.
- Case studies.
- Work samples.
- Project descriptions.
- Skills demonstrated.
- Problem-solving explanations.
- Results and impact.
- Visual presentation.
- Professional storytelling.
- Navigation and clarity.
- Missing project details.
- Contact and social links.

For non-technical users, portfolio evidence can include marketing campaigns, writing samples, design work, business projects, HR initiatives, sales achievements, and other relevant proof.

### 11. LinkedIn Profile Analysis

Users can upload a LinkedIn PDF, paste profile content, or provide exported profile data.

The system evaluates headline, About section, experience descriptions, skills, certifications, featured content, project presentation, keyword coverage, recruiter discoverability, completeness, and alignment with the target role.

Direct unauthorized LinkedIn scraping is out of scope.

### 12. LinkedIn Profile Optimization

The platform can generate improved LinkedIn headline, rewritten About section, improved experience descriptions, suggested skills, suggested featured projects, certification recommendations, keyword recommendations, and profile-completeness improvements.

Users can generate only the sections they need.

### 17. Personalized Project Recommendations

The system recommends practical projects that close skill gaps.

Each project can include title, problem statement, target specialization, demonstrated skills, features to build, tools, difficulty, scope, learning objectives, deliverables, resume bullet example, portfolio advice, and connection to job requirements.

Examples include QA automation framework, REST API system, campaign analytics project, recruitment dashboard, sales pipeline analysis, credit-risk dashboard, and customer-retention analysis.

### 18. Personalized Career Roadmap

The platform creates a structured roadmap based on current specialization, target specialization, career objective, skill gaps, available study time, experience level, and target jobs.

Durations can include 7-day, 30-day, 90-day, and six-month plans.

### 19. Daily, Weekly, and Monthly Learning Plans

Users can receive detailed schedules with daily tasks, weekly goals, monthly milestones, study topics, practice activities, projects, review sessions, job-application activities, interview practice, and progress checkpoints.

### 24. Cover Letter Generation

The platform generates personalized cover letters for selected jobs. Outputs include standard, concise, entry-level, career-transition, and email application versions.

The system uses only candidate profile facts and must not fabricate experience or achievements.

### 25. Job-Specific Resume Tailoring

For a selected job, the platform recommends skills to emphasize, bullets to reorder, keywords to add, summary changes, projects to highlight, irrelevant information to reduce, missing evidence to add, and experience descriptions to rewrite.

### 31. Saved Analysis History

Registered users can save and reopen candidate profiles, resume analyses, job matches, skill-gap reports, roadmaps, cover letters, LinkedIn rewrites, interview sessions, and generated reports.

Cached results prevent repeated expensive AI analysis when inputs have not changed.

## Phase 3 Features

### 15. Job Matching

The platform retrieves and ranks jobs using structured filtering, semantic retrieval, and RAG.

Matching can consider specialization, skills, experience, seniority, industry, education, location, remote preference, employment type, career goal, and transferable skills.

Each matched job includes match score, matched skills, missing skills, relevant experience, concerns, explanation, and apply recommendation.

### 16. Explainable Job Recommendations

For each job, the system explains evidence supporting the match, fully met requirements, partially met requirements, missing requirements, candidate competitiveness, improvement actions, and resume sections to tailor.

### 20. Interview Preparation

The system generates personalized interview preparation based on resume, candidate profile, target job, portfolio, GitHub profile, experience level, and skill gaps.

Question categories include technical or role-specific, behavioral, situational, resume-based, project-based, portfolio-based, leadership, career-transition, and job-description-specific questions.

### 21. Interactive Mock Interview

The platform conducts conversational mock interviews:

1. AI asks a question.
2. User answers.
3. AI evaluates the answer.
4. AI asks a relevant follow-up.
5. User receives feedback.

Feedback covers accuracy, relevance, clarity, structure, evidence, technical depth, confidence, missing details, and suggested improvement.

### 22. Resume Claim Verification Questions

The platform identifies important claims an interviewer may ask about, such as technologies used, leadership claims, project ownership, performance improvements, revenue or sales impact, automation experience, collaboration, architecture, testing, certifications, tools, and methodologies.

The platform reports evidence strength, claim-verification confidence, inconsistencies, claims requiring clarification, and questions the candidate should prepare to answer.

It must not claim to detect lies.

### 23. Answer Evaluation

Users can submit interview answers. The system evaluates whether the answer addresses the question, uses specific examples, remains consistent with the resume, uses STAR effectively, includes credible technical details, demonstrates impact, and withstands likely follow-ups.

It provides improved answer structure without inventing experience.

### 26. Recruiter Outreach Content

The platform can generate LinkedIn connection messages, recruiter outreach messages, job-application emails, follow-up emails, interview thank-you emails, referral requests, and short professional introductions.

All generated messages use the existing candidate profile.

### 27. Career Transition Analysis

For career changers, the system identifies transferable skills, reframed experience, relevant past work, missing foundational knowledge, suitable transitional roles, recommended projects, realistic learning sequence, resume positioning, and likely interview concerns.

### Advanced Privacy And Data Controls

Phase 3 completes privacy controls:

- Temporary-file deletion.
- Optional deletion after parsing.
- Delete-my-data control.
- Clear data-retention status.
- Exportable user data.
- Audit-friendly privacy events.
