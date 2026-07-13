import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ResumeWorkflow } from "@/features/resume/ResumeWorkflow";

const originalFetch = globalThis.fetch;

afterEach(() => {
  cleanup();
  globalThis.fetch = originalFetch;
  vi.restoreAllMocks();
});

describe("ResumeWorkflow", () => {
  it("asks the user to sign in when no access token is available", () => {
    render(<ResumeWorkflow accessToken={null} />);

    expect(screen.getByText(/Sign in to create a profile and upload a resume/i)).toBeInTheDocument();
  });

  it("shows profile fields when signed in", () => {
    render(<ResumeWorkflow accessToken="token" />);

    expect(screen.getByLabelText(/Career goal/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Preferred role/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Create profile/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Load latest profile/i })).toBeInTheDocument();
  });

  it("loads the latest profile and saved outputs after refresh", async () => {
    const user = userEvent.setup();
    mockFetch([
      [
        {
          id: "profile-id",
          career_goal: "Prepare for a target role",
          preferred_role: "Operations Analyst",
          profile_status: "draft",
        },
      ],
      [
        {
          id: "output-id",
          output_type: "ai_interview_prep",
          job_description_id: null,
          prompt_version: "ai-interview-prep-v1",
          provider: "local_template",
          model_name: "local-template-v1",
          result_json: { summary: "Saved interview prep summary." },
          result_markdown: "# Snipe Interview Prep",
          status: "completed",
          created_at: "2026-07-13T12:00:00Z",
        },
      ],
      [],
    ]);
    render(<ResumeWorkflow accessToken="token" />);

    await user.click(screen.getByRole("button", { name: /Load latest profile/i }));

    expect(await screen.findByText(/Profile ready for Operations Analyst/i)).toBeInTheDocument();
    expect(screen.getByText("Saved interview prep summary.")).toBeInTheDocument();
  });

  it("reuses a saved target job for skill gap analysis", async () => {
    const user = userEvent.setup();
    const fetchMock = mockFetch([
      [
        {
          id: "profile-id",
          career_goal: "Prepare for a target role",
          preferred_role: "Operations Analyst",
          profile_status: "draft",
        },
      ],
      [],
      [
        {
          id: "job-id",
          profile_id: "profile-id",
          source_type: "pasted_text",
          input_hash: "job-hash",
          structured: {
            parser_version: "deterministic-job-parser-v1",
            title: "Senior Operations Analyst",
            company: "Acme Logistics",
            required_skills: ["excel", "sql"],
            preferred_skills: ["tableau"],
            tools: ["tableau"],
            soft_skills: ["communication"],
            responsibilities: ["Lead reporting"],
            education: [],
            experience_requirements: [],
            seniority: "senior",
            ats_keywords: ["excel", "sql", "tableau"],
          },
        },
      ],
      {
        source_id: "source-id",
        profile_id: "profile-id",
        source_type: "resume",
        original_filename: "resume.pdf",
        storage_path: "candidate-documents/resume.pdf",
        content_hash: "content-hash",
        parsed_text_hash: "parsed-hash",
        parser_version: "test-parser",
        status: "parsed",
        text_length: 1200,
        page_count: 1,
        paragraph_count: 8,
        profile_version: 1,
        evidence_count: 4,
        normalized_profile_updated: true,
      },
      {
        analysis_type: "skill_gap",
        deterministic_version: "deterministic-skill-gap-v1",
        score: 70,
        matched_skills: [{ skill: "excel", category: "required", importance: "high", evidence: "resume" }],
        partially_matched_skills: [],
        missing_skills: [{ skill: "sql", category: "required", importance: "high", evidence: null }],
        transferable_skills: [],
        claimed_but_unverified_skills: [],
        not_relevant_skills: [],
        checks: { has_job_skills: true },
      },
    ]);
    render(<ResumeWorkflow accessToken="token" />);

    await user.click(screen.getByRole("button", { name: /Load latest profile/i }));
    const fileInput = await screen.findByLabelText(/Upload resume/i);
    const file = new File(["resume content"], "resume.pdf", { type: "application/pdf" });
    await user.upload(fileInput, file);
    await user.selectOptions(await screen.findByLabelText(/Saved target jobs/i), "job-id");
    await user.click(await screen.findByRole("button", { name: /Run skill gap analysis/i }));

    expect(await screen.findByText("Skill gap")).toBeInTheDocument();
    expect(screen.getByText("sql")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenLastCalledWith(
      expect.stringContaining("/profiles/profile-id/analyses/skill-gap"),
      expect.objectContaining({
        body: JSON.stringify({ job_description_id: "job-id" }),
      }),
    );
  });

  it("groups post-upload actions by workflow area", async () => {
    const user = userEvent.setup();
    mockFetch([
      {
        id: "profile-id",
        career_goal: "Prepare for a target role",
        preferred_role: "Operations Analyst",
        profile_status: "draft",
      },
      {
        source_id: "source-id",
        profile_id: "profile-id",
        source_type: "resume",
        original_filename: "resume.pdf",
        storage_path: "candidate-documents/resume.pdf",
        content_hash: "content-hash",
        parsed_text_hash: "parsed-hash",
        parser_version: "test-parser",
        status: "parsed",
        text_length: 1200,
        page_count: 1,
        paragraph_count: 8,
        profile_version: 1,
        evidence_count: 4,
        normalized_profile_updated: true,
      },
    ]);
    render(<ResumeWorkflow accessToken="token" />);

    await user.type(screen.getByLabelText(/Preferred role/i), "Operations Analyst");
    await user.click(screen.getByRole("button", { name: /Create profile/i }));
    const fileInput = await screen.findByLabelText(/Upload resume/i);
    const file = new File(["resume content"], "resume.pdf", { type: "application/pdf" });
    await user.upload(fileInput, file);

    expect(await screen.findByText("Analysis")).toBeInTheDocument();
    expect(screen.getByText("Saved outputs")).toBeInTheDocument();
    expect(screen.getByText("AI generation")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Resume quality/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Job matches/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Full report/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Data summary/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Delete documents only/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Load history/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Regenerate prep/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Claim questions/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Regenerate claims/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Mock interview/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Outreach messages/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Career transition/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Project roadmap$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Regenerate roadmap/i })).toBeInTheDocument();
  });

  it("renders saved-output filters and management controls after history loads", async () => {
    const user = userEvent.setup();
    mockFetch([
      {
        id: "profile-id",
        career_goal: "Prepare for a target role",
        preferred_role: "Operations Analyst",
        profile_status: "draft",
      },
      {
        source_id: "source-id",
        profile_id: "profile-id",
        source_type: "resume",
        original_filename: "resume.pdf",
        storage_path: "candidate-documents/resume.pdf",
        content_hash: "content-hash",
        parsed_text_hash: "parsed-hash",
        parser_version: "test-parser",
        status: "parsed",
        text_length: 1200,
        page_count: 1,
        paragraph_count: 8,
        profile_version: 1,
        evidence_count: 4,
        normalized_profile_updated: true,
      },
      {
        id: "job-id",
        profile_id: "profile-id",
        source_type: "pasted_text",
        input_hash: "job-hash",
        structured: {
          parser_version: "deterministic-job-parser-v1",
          title: "Operations Analyst",
          company: "Acme Logistics",
          required_skills: ["excel", "sql"],
          preferred_skills: [],
          tools: ["excel"],
          soft_skills: ["communication"],
          responsibilities: ["Build operations reports"],
          education: [],
          experience_requirements: [],
          seniority: null,
          ats_keywords: ["excel", "sql", "operations"],
        },
      },
      [
        {
          id: "output-id",
          output_type: "ai_interview_prep",
          job_description_id: "job-id",
          prompt_version: "ai-interview-prep-v1",
          provider: "local_template",
          model_name: "local-template-v1",
          result_json: { summary: "Interview prep summary." },
          result_markdown: "# Snipe Interview Prep",
          status: "completed",
          created_at: "2026-07-13T12:00:00Z",
        },
        {
          id: "general-output-id",
          output_type: "ai_resume_rewrite_suggestions",
          job_description_id: null,
          prompt_version: "ai-resume-rewrite-suggestions-v1",
          provider: "local_template",
          model_name: "local-template-v1",
          result_json: { summary: "General rewrite summary." },
          result_markdown: "# Snipe Resume Rewrite Suggestions",
          status: "completed",
          created_at: "2026-07-13T12:05:00Z",
        },
      ],
    ]);
    render(<ResumeWorkflow accessToken="token" />);

    await user.type(screen.getByLabelText(/Preferred role/i), "Operations Analyst");
    await user.click(screen.getByRole("button", { name: /Create profile/i }));
    const fileInput = await screen.findByLabelText(/Upload resume/i);
    const file = new File(["resume content"], "resume.pdf", { type: "application/pdf" });
    await user.upload(fileInput, file);
    await user.type(
      screen.getByPlaceholderText("Paste a target job description here."),
      "Operations Analyst at Acme Logistics. Requirements include Excel, SQL, communication, and operations reporting. Responsibilities include building reports and improving workflows.",
    );
    await user.click(screen.getByRole("button", { name: /Analyze job description/i }));
    await user.click(await screen.findByRole("button", { name: /Load history/i }));

    expect(await screen.findByText("Interview prep summary.")).toBeInTheDocument();
    expect(screen.getByText("General rewrite summary.")).toBeInTheDocument();
    expect(screen.getByLabelText("Type")).toHaveValue("all");
    expect(screen.getByText("Active target: Operations Analyst at Acme Logistics")).toBeInTheDocument();
    await user.selectOptions(screen.getByLabelText("Type"), "active_target");
    expect(screen.getByText("Interview prep summary.")).toBeInTheDocument();
    expect(screen.queryByText("General rewrite summary.")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /View details/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Copy markdown/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Download \.md/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Delete$/i })).toBeInTheDocument();
  });

  it("adds and searches reference library documents", async () => {
    const user = userEvent.setup();
    const fetchMock = mockFetch([
      {
        id: "profile-id",
        career_goal: "Prepare for a target role",
        preferred_role: "Data Analyst",
        profile_status: "draft",
      },
      {
        document_id: "doc-1",
        title: "Data Analyst Job Listing",
        source_type: "job_listing",
        content_hash: "content-hash",
        chunk_count: 2,
        embedding_model: "deterministic-hashing-v1",
      },
      {
        query: "python sql analytics",
        embedding_model: "deterministic-hashing-v1",
        citations: [
          {
            document_id: "doc-1",
            chunk_id: "chunk-1",
            title: "Data Analyst Job Listing",
            source_type: "job_listing",
            source_url: "https://example.com/jobs/data",
            chunk_index: 0,
            content: "Python SQL analytics dashboards stakeholder reporting.",
            score: 0.91,
            metadata: {},
          },
        ],
      },
    ]);
    render(<ResumeWorkflow accessToken="token" />);

    await user.type(screen.getByLabelText(/Preferred role/i), "Data Analyst");
    await user.click(screen.getByRole("button", { name: /Create profile/i }));
    await user.type(await screen.findByLabelText(/^Title$/i), "Data Analyst Job Listing");
    await user.selectOptions(screen.getByLabelText(/Source type/i), "job_listing");
    await user.type(screen.getByLabelText(/Source URL/i), "https://example.com/jobs/data");
    await user.type(
      screen.getByLabelText(/Reference text/i),
      "Python SQL analytics dashboards stakeholder reporting ".repeat(4),
    );
    await user.click(screen.getByRole("button", { name: /Add reference/i }));

    expect(await screen.findByText(/Added Data Analyst Job Listing as 2 searchable chunk/i)).toBeInTheDocument();
    await user.clear(screen.getByLabelText(/^Query$/i));
    await user.type(screen.getByLabelText(/^Query$/i), "python sql analytics");
    await user.selectOptions(screen.getByLabelText(/Reference results/i), "5");
    await user.click(screen.getByRole("button", { name: /Search references/i }));

    expect(await screen.findByText("Python SQL analytics dashboards stakeholder reporting.")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/rag/documents"),
      expect.objectContaining({ method: "POST" }),
    );
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/rag/search"),
      expect.objectContaining({
        body: JSON.stringify({
          source_types: [],
          limit: 5,
          query: "python sql analytics",
        }),
      }),
    );
  });

  it("opens and deletes a saved output", async () => {
    const user = userEvent.setup();
    const fetchMock = mockFetch([
      {
        id: "profile-id",
        career_goal: "Prepare for a target role",
        preferred_role: "Operations Analyst",
        profile_status: "draft",
      },
      {
        source_id: "source-id",
        profile_id: "profile-id",
        source_type: "resume",
        original_filename: "resume.pdf",
        storage_path: "candidate-documents/resume.pdf",
        content_hash: "content-hash",
        parsed_text_hash: "parsed-hash",
        parser_version: "test-parser",
        status: "parsed",
        text_length: 1200,
        page_count: 1,
        paragraph_count: 8,
        profile_version: 1,
        evidence_count: 4,
        normalized_profile_updated: true,
      },
      [
        {
          id: "output-id",
          output_type: "ai_application_materials",
          job_description_id: null,
          prompt_version: "ai-application-materials-v1",
          provider: "local_template",
          model_name: "local-template-v1",
          result_json: { summary: "Application materials summary." },
          result_markdown: "# Snipe Application Materials",
          status: "completed",
          created_at: "2026-07-13T12:00:00Z",
        },
      ],
      {
        id: "output-id",
        output_type: "ai_application_materials",
        job_description_id: null,
        prompt_version: "ai-application-materials-v1",
        provider: "local_template",
        model_name: "local-template-v1",
        result_json: { summary: "Application materials summary." },
        result_markdown: "# Snipe Application Materials\n\nCover letter text.",
        status: "completed",
        created_at: "2026-07-13T12:00:00Z",
      },
      { output_id: "output-id", deleted: true },
    ]);
    render(<ResumeWorkflow accessToken="token" />);

    await user.type(screen.getByLabelText(/Preferred role/i), "Operations Analyst");
    await user.click(screen.getByRole("button", { name: /Create profile/i }));
    const fileInput = await screen.findByLabelText(/Upload resume/i);
    const file = new File(["resume content"], "resume.pdf", { type: "application/pdf" });
    await user.upload(fileInput, file);
    await user.click(await screen.findByRole("button", { name: /Load history/i }));
    await user.click(await screen.findByRole("button", { name: /View details/i }));

    expect(await screen.findByText(/Cover letter text/i)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /^Delete$/i }));

    await waitFor(() => expect(screen.queryByText("Application materials summary.")).not.toBeInTheDocument());
    expect(screen.queryByText(/Cover letter text/i)).not.toBeInTheDocument();
    expect(fetchMock).toHaveBeenLastCalledWith(
      expect.stringContaining("/profiles/profile-id/generated-outputs/output-id"),
      expect.objectContaining({ method: "DELETE" }),
    );
  });

  it("renders generated project roadmap recommendations", async () => {
    const user = userEvent.setup();
    mockFetch([
      {
        id: "profile-id",
        career_goal: "Prepare for a target role",
        preferred_role: "Operations Analyst",
        profile_status: "draft",
      },
      {
        source_id: "source-id",
        profile_id: "profile-id",
        source_type: "resume",
        original_filename: "resume.pdf",
        storage_path: "candidate-documents/resume.pdf",
        content_hash: "content-hash",
        parsed_text_hash: "parsed-hash",
        parser_version: "test-parser",
        status: "parsed",
        text_length: 1200,
        page_count: 1,
        paragraph_count: 8,
        profile_version: 1,
        evidence_count: 4,
        normalized_profile_updated: true,
      },
      {
        output_type: "ai_project_roadmap_recommendations",
        output_version: "ai-project-roadmap-v1",
        provider: "local_template",
        model_name: "local-template-v1",
        summary: "Project roadmap generated from verified skills.",
        projects: [
          {
            title: "Operations dashboard case study",
            objective: "Build future proof for verified Excel and SQL skills.",
            skills_practiced: ["excel", "sql"],
            deliverables: ["case study"],
            evidence_to_add: ["project link"],
            missing_evidence_warning: null,
          },
        ],
        roadmap: [
          {
            timeframe: "7_day",
            focus: "Scope one realistic project.",
            actions: ["Choose a project tied to verified skills."],
            success_criteria: ["scope is documented"],
          },
        ],
        missing_evidence_warnings: ["Add communication only if supported by real evidence."],
        cautions: ["Do not present recommended projects as completed."],
        cached: false,
      },
      [],
    ]);
    render(<ResumeWorkflow accessToken="token" />);

    await user.type(screen.getByLabelText(/Preferred role/i), "Operations Analyst");
    await user.click(screen.getByRole("button", { name: /Create profile/i }));
    const fileInput = await screen.findByLabelText(/Upload resume/i);
    const file = new File(["resume content"], "resume.pdf", { type: "application/pdf" });
    await user.upload(fileInput, file);
    await user.click(await screen.findByRole("button", { name: /^Project roadmap$/i }));

    expect(await screen.findByText("Project roadmap generated from verified skills.")).toBeInTheDocument();
    expect(screen.getByText("Operations dashboard case study")).toBeInTheDocument();
    expect(screen.getByText("7-day plan")).toBeInTheDocument();
    expect(screen.getByText("Do not present recommended projects as completed.")).toBeInTheDocument();
  });

  it("renders deterministic job matches", async () => {
    const user = userEvent.setup();
    const fetchMock = mockFetch([
      {
        id: "profile-id",
        career_goal: "Prepare for a target role",
        preferred_role: "Data Analyst",
        profile_status: "draft",
      },
      {
        source_id: "source-id",
        profile_id: "profile-id",
        source_type: "resume",
        original_filename: "resume.pdf",
        storage_path: "candidate-documents/resume.pdf",
        content_hash: "content-hash",
        parsed_text_hash: "parsed-hash",
        parser_version: "test-parser",
        status: "parsed",
        text_length: 1200,
        page_count: 1,
        paragraph_count: 8,
        profile_version: 1,
        evidence_count: 4,
        normalized_profile_updated: true,
      },
      {
        analysis_type: "job_match",
        deterministic_version: "deterministic-job-matcher-v1",
        query: "Data Analyst",
        match_count: 1,
        matches: [
          {
            job_reference_id: "job-1",
            title: "Data Analyst",
            company: null,
            match_score: 88,
            semantic_score: 0.9,
            skill_alignment_score: 86,
            matched_skills: ["python", "sql", "excel"],
            partially_matched_skills: [],
            missing_skills: ["tableau"],
            relevant_experience: ["Profile evidence mentions sql."],
            concerns: ["Missing required skills: tableau."],
            explanation: "Data Analyst scored 88 because the profile matches python, sql, excel.",
            apply_recommendation: "apply_with_tailoring",
            structured_job: {
              parser_version: "deterministic-job-parser-v1",
              title: "Data Analyst",
              company: null,
              required_skills: ["python", "sql", "excel", "tableau"],
              preferred_skills: [],
              tools: ["tableau"],
              soft_skills: [],
              responsibilities: ["Build dashboards"],
              education: [],
              experience_requirements: [],
              seniority: null,
              ats_keywords: ["python", "sql", "excel", "tableau"],
            },
            source_excerpt:
              "Data Analyst Requirements Python, SQL, Excel, Tableau. Responsibilities Build dashboards, collaborate with stakeholders, and improve reporting workflows.",
            citation: {
              document_id: "job-1",
              chunk_id: "chunk-1",
              title: "Analytics job listing",
              source_type: "job_listing",
              source_url: "https://example.com/jobs/data",
              score: 0.9,
            },
          },
        ],
        checks: {
          uses_deterministic_ranking: true,
          uses_source_citations: true,
        },
      },
      {
        id: "target-job-id",
        profile_id: "profile-id",
        source_type: "pasted_text",
        input_hash: "target-job-hash",
        structured: {
          parser_version: "deterministic-job-parser-v1",
          title: "Data Analyst",
          company: null,
          required_skills: ["python", "sql", "excel", "tableau"],
          preferred_skills: [],
          tools: ["tableau"],
          soft_skills: [],
          responsibilities: ["Build dashboards"],
          education: [],
          experience_requirements: [],
          seniority: null,
          ats_keywords: ["python", "sql", "excel", "tableau"],
        },
      },
      {
        id: "target-job-id-2",
        profile_id: "profile-id",
        source_type: "pasted_text",
        input_hash: "target-job-hash-2",
        structured: {
          parser_version: "deterministic-job-parser-v1",
          title: "Data Analyst",
          company: null,
          required_skills: ["python", "sql", "excel", "tableau"],
          preferred_skills: [],
          tools: ["tableau"],
          soft_skills: [],
          responsibilities: ["Build dashboards"],
          education: [],
          experience_requirements: [],
          seniority: null,
          ats_keywords: ["python", "sql", "excel", "tableau"],
        },
      },
      {
        output_type: "ai_resume_tailoring_package",
        output_version: "ai-resume-tailoring-package-v1",
        provider: "local_template",
        model_name: "local-template-v1",
        summary: "Tailoring generated for saved match.",
        tailored_summary: "Evidence-bound analyst summary.",
        skill_order: ["sql", "excel"],
        keyword_recommendations: [],
        missing_evidence_warnings: [],
        cautions: [],
        cached: false,
      },
      [],
    ]);
    render(<ResumeWorkflow accessToken="token" />);

    await user.type(screen.getByLabelText(/Preferred role/i), "Data Analyst");
    await user.click(screen.getByRole("button", { name: /Create profile/i }));
    const fileInput = await screen.findByLabelText(/Upload resume/i);
    const file = new File(["resume content"], "resume.pdf", { type: "application/pdf" });
    await user.upload(fileInput, file);
    await user.type(await screen.findByLabelText(/Search query/i), "remote analytics sql");
    await user.selectOptions(screen.getByLabelText(/^Results$/i), "5");
    await user.click(screen.getByRole("button", { name: /Run job match search/i }));

    expect(await screen.findByRole("heading", { name: "Job matches" })).toBeInTheDocument();
    expect(screen.getAllByText("Data Analyst").length).toBeGreaterThan(0);
    expect(screen.getByText("Apply with tailoring")).toBeInTheDocument();
    expect(screen.getByText(/Analytics job listing/)).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/profiles/profile-id/job-matches"),
      expect.objectContaining({
        body: JSON.stringify({ query: "remote analytics sql", limit: 5 }),
      }),
    );
    await user.click(screen.getByRole("button", { name: /Save as target job/i }));

    expect(await screen.findByText("Job match saved as the active target job.")).toBeInTheDocument();
    expect(screen.getByText("Active target selected")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /^Generate tailoring$/i }));

    expect(await screen.findByText("Tailoring generated for saved match.")).toBeInTheDocument();
    expect(screen.getByText("Job match saved and tailoring package generated.")).toBeInTheDocument();
  });

  it("renders generated claim verification questions", async () => {
    const user = userEvent.setup();
    mockFetch([
      {
        id: "profile-id",
        career_goal: "Prepare for a target role",
        preferred_role: "Data Analyst",
        profile_status: "draft",
      },
      {
        source_id: "source-id",
        profile_id: "profile-id",
        source_type: "resume",
        original_filename: "resume.pdf",
        storage_path: "candidate-documents/resume.pdf",
        content_hash: "content-hash",
        parsed_text_hash: "parsed-hash",
        parser_version: "test-parser",
        status: "parsed",
        text_length: 1200,
        page_count: 1,
        paragraph_count: 8,
        profile_version: 1,
        evidence_count: 4,
        normalized_profile_updated: true,
      },
      {
        output_type: "ai_claim_verification_questions",
        output_version: "ai-claim-verification-v1",
        provider: "deterministic",
        model_name: "deterministic-claim-verification-v1",
        summary: "Claim questions generated with evidence-strength notes.",
        questions: [
          {
            claim: "python",
            evidence_strength: "strong",
            question: "What specific example proves your experience with python?",
            why_it_matters: "Interviewers often ask for scope and outcomes.",
            evidence_to_prepare: ["A real task involving python."],
            caution: null,
          },
        ],
        evidence_strength_notes: ["Strong evidence means the profile includes a specific excerpt."],
        cautions: ["Do not add unsupported metrics."],
        cached: false,
      },
      [],
    ]);
    render(<ResumeWorkflow accessToken="token" />);

    await user.type(screen.getByLabelText(/Preferred role/i), "Data Analyst");
    await user.click(screen.getByRole("button", { name: /Create profile/i }));
    const fileInput = await screen.findByLabelText(/Upload resume/i);
    const file = new File(["resume content"], "resume.pdf", { type: "application/pdf" });
    await user.upload(fileInput, file);
    await user.click(await screen.findByRole("button", { name: /^Claim questions$/i }));

    expect(await screen.findByRole("heading", { name: "Claim questions" })).toBeInTheDocument();
    expect(screen.getByText("strong")).toBeInTheDocument();
    expect(screen.getByText(/What specific example proves/)).toBeInTheDocument();
    expect(screen.queryByText(/lie detector/i)).not.toBeInTheDocument();
  });

  it("runs a mock interview turn", async () => {
    const user = userEvent.setup();
    const session = {
      session_id: "session-1",
      version: "deterministic-mock-interview-v1",
      status: "active",
      current_index: 0,
      questions: [
        {
          category: "technical",
          question: "Tell me about a real example where you used SQL.",
          evidence_to_use: ["Built SQL dashboards."],
        },
      ],
      transcript: [],
    };
    mockFetch([
      {
        id: "profile-id",
        career_goal: "Prepare for a target role",
        preferred_role: "Data Analyst",
        profile_status: "draft",
      },
      {
        source_id: "source-id",
        profile_id: "profile-id",
        source_type: "resume",
        original_filename: "resume.pdf",
        storage_path: "candidate-documents/resume.pdf",
        content_hash: "content-hash",
        parsed_text_hash: "parsed-hash",
        parser_version: "test-parser",
        status: "parsed",
        text_length: 1200,
        page_count: 1,
        paragraph_count: 8,
        profile_version: 1,
        evidence_count: 4,
        normalized_profile_updated: true,
      },
      session,
      {
        session: {
          ...session,
          status: "completed",
          current_index: 1,
          transcript: [
            {
              question: session.questions[0],
              answer: "I built SQL dashboards.",
              evaluation: {
                output_type: "interview_answer_evaluation",
                output_version: "deterministic-answer-evaluation-v1",
                relevance_score: 70,
                clarity_score: 85,
                evidence_score: 80,
                depth_score: 50,
                confidence_score: 85,
                overall_score: 72,
                star_feedback: ["Situation: missing."],
                strengths: ["The answer uses evidence connected to the profile."],
                improvements: ["Add scope, action, and result details using the STAR method."],
                improved_answer: "I would strengthen this with STAR details.",
                follow_up_question: "What was your exact role?",
                cautions: ["Do not add unsupported metrics."],
              },
              follow_up_question: "What was your exact role?",
            },
          ],
        },
        evaluation: {
          output_type: "interview_answer_evaluation",
          output_version: "deterministic-answer-evaluation-v1",
          relevance_score: 70,
          clarity_score: 85,
          evidence_score: 80,
          depth_score: 50,
          confidence_score: 85,
          overall_score: 72,
          star_feedback: ["Situation: missing."],
          strengths: ["The answer uses evidence connected to the profile."],
          improvements: ["Add scope, action, and result details using the STAR method."],
          improved_answer: "I would strengthen this with STAR details.",
          follow_up_question: "What was your exact role?",
          cautions: ["Do not add unsupported metrics."],
        },
        follow_up_question: "What was your exact role?",
        next_question: null,
      },
    ]);
    render(<ResumeWorkflow accessToken="token" />);

    await user.type(screen.getByLabelText(/Preferred role/i), "Data Analyst");
    await user.click(screen.getByRole("button", { name: /Create profile/i }));
    const fileInput = await screen.findByLabelText(/Upload resume/i);
    const file = new File(["resume content"], "resume.pdf", { type: "application/pdf" });
    await user.upload(fileInput, file);
    await user.click(await screen.findByRole("button", { name: /^Mock interview$/i }));

    expect(await screen.findByText("Tell me about a real example where you used SQL.")).toBeInTheDocument();
    await user.type(screen.getByPlaceholderText("Type your answer here."), "I built SQL dashboards.");
    await user.click(screen.getByRole("button", { name: /Submit answer/i }));

    expect(await screen.findByText("Latest evaluation")).toBeInTheDocument();
    expect(screen.getByText("What was your exact role?")).toBeInTheDocument();
    expect(screen.getByText(/Completed 1 interview turns/i)).toBeInTheDocument();
  });

  it("renders privacy summary and generated full report", async () => {
    const user = userEvent.setup();
    mockFetch([
      {
        id: "profile-id",
        career_goal: "Prepare for a target role",
        preferred_role: "Operations Analyst",
        profile_status: "draft",
      },
      {
        source_id: "source-id",
        profile_id: "profile-id",
        source_type: "resume",
        original_filename: "resume.pdf",
        storage_path: "candidate-documents/resume.pdf",
        content_hash: "content-hash",
        parsed_text_hash: "parsed-hash",
        parser_version: "test-parser",
        status: "parsed",
        text_length: 1200,
        page_count: 1,
        paragraph_count: 8,
        profile_version: 1,
        evidence_count: 4,
        normalized_profile_updated: true,
      },
      {
        profile_id: "profile-id",
        profile_exists: true,
        stored_document_count: 1,
        generated_output_count: 3,
        retention_policy: "Raw uploaded documents are private.",
      },
      {
        report_type: "full_career_report",
        report_version: "full-career-report-v1",
        title: "Snipe Full Career Report: Operations Analyst",
        summary: "Full career report includes saved generated outputs.",
        sections_included: ["readiness", "strengths", "ai_interview_prep"],
        markdown: "# Snipe Full Career Report\n\n## Saved AI Outputs",
      },
      [],
    ]);
    render(<ResumeWorkflow accessToken="token" />);

    await user.type(screen.getByLabelText(/Preferred role/i), "Operations Analyst");
    await user.click(screen.getByRole("button", { name: /Create profile/i }));
    const fileInput = await screen.findByLabelText(/Upload resume/i);
    const file = new File(["resume content"], "resume.pdf", { type: "application/pdf" });
    await user.upload(fileInput, file);
    await user.click(await screen.findByRole("button", { name: /Data summary/i }));

    expect(await screen.findByText("Raw uploaded documents are private.")).toBeInTheDocument();
    expect(screen.getAllByText("3").length).toBeGreaterThan(0);

    await user.click(screen.getByRole("button", { name: /Full report/i }));

    expect(await screen.findByText("Snipe Full Career Report: Operations Analyst")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Download full report/i })).toBeInTheDocument();
    expect(screen.getByText(/Saved AI Outputs/i)).toBeInTheDocument();
  });
});

function mockFetch(responses: unknown[]) {
  const fetchMock = vi.fn(async () => {
    const body = responses.shift();
    return new Response(JSON.stringify(body), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  });
  globalThis.fetch = fetchMock;
  return fetchMock;
}
