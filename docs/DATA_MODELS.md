# Data Models

## Candidate Profile Principle

The normalized candidate profile is the central reusable model. It is created from the required resume and enriched by optional GitHub, LinkedIn, portfolio, target-role, and user-entered data.

All downstream features consume this profile instead of repeatedly sending raw resumes or raw documents to AI providers.

## Normalized Candidate Profile

Conceptual structure:

```text
CandidateProfile
  id
  user_id
  version
  profile_status
  career_goal
  preferred_role
  target_specialization
  target_seniority
  location_preference
  remote_preference
  availability
  source_summary
  contact
  professional_summary
  specializations
  seniority_estimate
  skills
  work_experiences
  projects
  education
  certifications
  languages
  achievements
  portfolio_items
  github_summary
  linkedin_summary
  evidence
  completeness
  risk_flags
  created_at
  updated_at
```

## Evidence Model

Every important profile fact should be traceable to evidence.

```text
Evidence
  id
  profile_id
  source_id
  source_type
  fact_type
  fact_id
  quote_or_excerpt
  normalized_value
  confidence
  page_number
  section_name
  url
  created_at
```

Source types:

- resume_pdf.
- resume_docx.
- github.
- portfolio.
- linkedin_pdf.
- linkedin_export.
- linkedin_pasted_text.
- user_input.
- job_description.
- rag_reference.

## Core Database Entities

### users

Managed primarily through Supabase Auth.

Application profile fields:

- id.
- email.
- display_name.
- created_at.
- updated_at.

### candidate_profiles

- id.
- user_id.
- version.
- career_goal.
- preferred_role.
- target_specialization.
- target_seniority.
- location_preference.
- remote_preference.
- profile_status.
- normalized_json.
- completeness_score.
- created_at.
- updated_at.

### profile_sources

- id.
- profile_id.
- user_id.
- source_type.
- storage_path.
- original_filename.
- content_hash.
- parsed_text_hash.
- parser_version.
- status.
- retention_policy.
- delete_after_parsing.
- created_at.
- parsed_at.
- deleted_at.

### profile_evidence

- id.
- profile_id.
- source_id.
- fact_type.
- fact_key.
- excerpt.
- normalized_value.
- confidence.
- location_json.
- created_at.

### skills

- id.
- canonical_name.
- category.
- aliases.
- profession_tags.
- created_at.

### profile_skills

- id.
- profile_id.
- skill_id.
- source.
- proficiency_estimate.
- evidence_strength.
- years_estimate.
- last_used_estimate.
- verified_status.
- created_at.

Verified status values:

- verified.
- partially_verified.
- claimed_unverified.
- inferred.

### work_experiences

- id.
- profile_id.
- company.
- title.
- start_date.
- end_date.
- current_role.
- location.
- description.
- achievements_json.
- skills_json.
- evidence_ids.

### projects

- id.
- profile_id.
- title.
- source_type.
- url.
- description.
- role.
- skills_json.
- outcomes_json.
- evidence_ids.

### education

- id.
- profile_id.
- institution.
- degree.
- field.
- start_date.
- end_date.
- evidence_ids.

### certifications

- id.
- profile_id.
- name.
- issuer.
- issue_date.
- expiration_date.
- credential_url.
- evidence_ids.

### job_descriptions

- id.
- user_id.
- profile_id.
- title.
- company.
- source_type.
- raw_text_hash.
- structured_json.
- required_skills.
- preferred_skills.
- responsibilities.
- seniority_expectations.
- location.
- employment_type.
- created_at.

### analyses

- id.
- user_id.
- profile_id.
- analysis_type.
- input_hash.
- profile_version.
- job_description_id.
- deterministic_version.
- ai_prompt_version.
- model_provider.
- model_name.
- result_json.
- score.
- status.
- created_at.

Analysis types:

- resume_quality.
- ats_readiness.
- specialization_detection.
- profile_completeness.
- skill_gap.
- job_match.
- portfolio_strength.
- interview_readiness.
- career_transition.

### generated_outputs

- id.
- user_id.
- profile_id.
- output_type.
- job_description_id.
- input_hash.
- prompt_version.
- provider.
- model_name.
- result_json.
- result_markdown.
- evidence_ids.
- status.
- created_at.
- updated_at.

Output types:

- resume_bullet_rewrite.
- professional_summary.
- linkedin_headline.
- linkedin_about.
- linkedin_experience.
- cover_letter.
- tailored_resume_recommendations.
- project_recommendations.
- career_roadmap.
- learning_plan.
- interview_questions.
- mock_interview_feedback.
- answer_evaluation.
- recruiter_message.
- career_report.

### rag_documents

- id.
- source_type.
- title.
- uri.
- version.
- metadata_json.
- created_at.

### rag_chunks

- id.
- document_id.
- chunk_index.
- text.
- embedding.
- metadata_json.
- created_at.

### usage_events

Anonymous product telemetry used for aggregate feature-health analysis.

- id.
- anonymous_session_id.
- event_name.
- surface.
- metadata.
- path.
- created_at.

This table intentionally does not include `user_id`, `profile_id`, email, raw
resume text, job-description text, generated AI output, document content, source
URLs, API keys, or JWTs.

### reports

- id.
- user_id.
- profile_id.
- report_type.
- input_hash.
- storage_path.
- included_sections.
- generated_output_ids.
- created_at.

## Relationships

- One user has many candidate profiles.
- One candidate profile has many profile sources.
- One candidate profile has many evidence records.
- One candidate profile has many skills, experiences, projects, education records, and certifications.
- One candidate profile has many job descriptions.
- One candidate profile has many analyses and generated outputs.
- Analyses and generated outputs may reference one target job description.
- Evidence records connect profile facts back to sources.
- RAG chunks are independent reference data but can be cited by generated outputs.
- Usage events are intentionally not related to users or candidate profiles.

## Profile Versioning

Every material profile update increments `candidate_profiles.version`.

Version increments are required when:

- A new resume is uploaded.
- Optional source data changes.
- User edits a profile fact.
- A parser version changes and reprocessing updates facts.
- Evidence attached to facts changes.

Cached analyses and generated outputs must record the profile version used.

## Sensitive Data Handling

- Raw documents stay in private storage.
- Parsed raw text should be stored only if needed and protected; normalized profile facts are preferred.
- Logs must contain IDs, hashes, and status values instead of raw document content.
- AI requests should include minimal structured context and evidence excerpts only when necessary.
