import { zodResolver } from "@hookform/resolvers/zod";
import {
  BriefcaseBusiness,
  ClipboardCheck,
  FileUp,
  Gauge,
  Github,
  GitCompareArrows,
  LayoutDashboard,
  Linkedin,
  LinkIcon,
  Plus,
  ScrollText,
  Sparkles,
  Trash2,
} from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import {
  BasicReportResult,
  AIInterpretationResult,
  CandidateProfile,
  DeterministicScoreResult,
  GitHubSourceResult,
  JobDescriptionResult,
  LinkedInSourceResult,
  PortfolioSourceResult,
  ReadinessDashboardResult,
  ResumeQualityResult,
  ResumeRewriteResult,
  ResumeUploadResult,
  SkillGapResult,
  addGitHubSource,
  addLinkedInTextSource,
  addPortfolioSource,
  createAIReadinessInterpretation,
  createBasicReport,
  createJobDescription,
  createResumeRewriteSuggestions,
  createProfile,
  deleteProfileData,
  runAtsReadinessAnalysis,
  runProfileCompletenessAnalysis,
  runReadinessDashboard,
  runResumeQualityAnalysis,
  runSkillGapAnalysis,
  uploadLinkedInSource,
  uploadResume,
} from "@/lib/api";

const profileSchema = z.object({
  career_goal: z.string().min(1, "Career goal is required.").max(120),
  preferred_role: z.string().min(1, "Preferred role is required.").max(120),
});

const jobDescriptionSchema = z.object({
  text: z.string().min(100, "Paste at least 100 characters from the job description.").max(60000),
});

const githubSchema = z.object({
  username_or_url: z.string().min(1, "GitHub username or URL is required.").max(120),
});

const portfolioSchema = z.object({
  url: z.string().min(1, "Portfolio URL is required.").max(500),
});

const linkedInSchema = z.object({
  text: z.string().min(50, "Paste at least 50 characters from LinkedIn.").max(60000),
});

type ProfileValues = z.infer<typeof profileSchema>;
type JobDescriptionValues = z.infer<typeof jobDescriptionSchema>;
type GitHubValues = z.infer<typeof githubSchema>;
type PortfolioValues = z.infer<typeof portfolioSchema>;
type LinkedInValues = z.infer<typeof linkedInSchema>;

type ResumeWorkflowProps = {
  accessToken: string | null;
};

export function ResumeWorkflow({ accessToken }: ResumeWorkflowProps) {
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [uploadResult, setUploadResult] = useState<ResumeUploadResult | null>(null);
  const [qualityResult, setQualityResult] = useState<ResumeQualityResult | null>(null);
  const [atsResult, setAtsResult] = useState<DeterministicScoreResult | null>(null);
  const [completenessResult, setCompletenessResult] = useState<DeterministicScoreResult | null>(null);
  const [jobResult, setJobResult] = useState<JobDescriptionResult | null>(null);
  const [githubResult, setGithubResult] = useState<GitHubSourceResult | null>(null);
  const [portfolioResult, setPortfolioResult] = useState<PortfolioSourceResult | null>(null);
  const [linkedInResult, setLinkedInResult] = useState<LinkedInSourceResult | null>(null);
  const [skillGapResult, setSkillGapResult] = useState<SkillGapResult | null>(null);
  const [dashboardResult, setDashboardResult] = useState<ReadinessDashboardResult | null>(null);
  const [reportResult, setReportResult] = useState<BasicReportResult | null>(null);
  const [aiInterpretationResult, setAiInterpretationResult] = useState<AIInterpretationResult | null>(null);
  const [rewriteResult, setRewriteResult] = useState<ResumeRewriteResult | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isBusy, setIsBusy] = useState(false);
  const form = useForm<ProfileValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      career_goal: "Prepare for a target role",
      preferred_role: "",
    },
  });
  const jobForm = useForm<JobDescriptionValues>({
    resolver: zodResolver(jobDescriptionSchema),
    defaultValues: {
      text: "",
    },
  });
  const githubForm = useForm<GitHubValues>({
    resolver: zodResolver(githubSchema),
    defaultValues: {
      username_or_url: "",
    },
  });
  const portfolioForm = useForm<PortfolioValues>({
    resolver: zodResolver(portfolioSchema),
    defaultValues: {
      url: "",
    },
  });
  const linkedInForm = useForm<LinkedInValues>({
    resolver: zodResolver(linkedInSchema),
    defaultValues: {
      text: "",
    },
  });

  async function handleCreateProfile(values: ProfileValues) {
    if (!accessToken) {
      setMessage("Sign in before creating a profile.");
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const created = await createProfile(accessToken, values);
      setProfile(created);
      setUploadResult(null);
      setQualityResult(null);
      setAtsResult(null);
      setCompletenessResult(null);
      setJobResult(null);
      setGithubResult(null);
      setPortfolioResult(null);
      setLinkedInResult(null);
      setSkillGapResult(null);
      setDashboardResult(null);
      setReportResult(null);
      setAiInterpretationResult(null);
      setRewriteResult(null);
      setMessage("Profile created.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not create profile.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleCreateJobDescription(values: JobDescriptionValues) {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const result = await createJobDescription(accessToken, profile.id, values.text);
      setJobResult(result);
      setSkillGapResult(null);
      setDashboardResult(null);
      setReportResult(null);
      setAiInterpretationResult(null);
      setRewriteResult(null);
      setMessage("Job description analyzed.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not analyze job description.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleAddGitHub(values: GitHubValues) {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const result = await addGitHubSource(accessToken, profile.id, values.username_or_url);
      setGithubResult(result);
      setMessage("GitHub source analyzed.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not analyze GitHub source.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleAddPortfolio(values: PortfolioValues) {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const result = await addPortfolioSource(accessToken, profile.id, values.url);
      setPortfolioResult(result);
      setMessage("Portfolio source analyzed.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not analyze portfolio source.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleAddLinkedInText(values: LinkedInValues) {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const result = await addLinkedInTextSource(accessToken, profile.id, values.text);
      setLinkedInResult(result);
      setMessage("LinkedIn source analyzed.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not analyze LinkedIn source.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleUploadLinkedIn(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file || !accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const result = await uploadLinkedInSource(accessToken, profile.id, file);
      setLinkedInResult(result);
      setMessage("LinkedIn upload analyzed.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not upload LinkedIn file.");
    } finally {
      setIsBusy(false);
      event.target.value = "";
    }
  }

  async function handleUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file || !accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const result = await uploadResume(accessToken, profile.id, file);
      setUploadResult(result);
      setQualityResult(null);
      setAtsResult(null);
      setCompletenessResult(null);
      setGithubResult(null);
      setPortfolioResult(null);
      setLinkedInResult(null);
      setSkillGapResult(null);
      setDashboardResult(null);
      setReportResult(null);
      setAiInterpretationResult(null);
      setRewriteResult(null);
      setMessage("Resume uploaded and parsed.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not upload resume.");
    } finally {
      setIsBusy(false);
      event.target.value = "";
    }
  }

  async function handleDeleteProfile() {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      await deleteProfileData(accessToken, profile.id);
      setProfile(null);
      setUploadResult(null);
      setQualityResult(null);
      setAtsResult(null);
      setCompletenessResult(null);
      setJobResult(null);
      setGithubResult(null);
      setPortfolioResult(null);
      setLinkedInResult(null);
      setSkillGapResult(null);
      setDashboardResult(null);
      setReportResult(null);
      setAiInterpretationResult(null);
      setRewriteResult(null);
      setMessage("Profile data deleted.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not delete profile data.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleCreateReport() {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const result = await createBasicReport(accessToken, profile.id, jobResult?.id ?? null);
      setReportResult(result);
      setMessage("Basic report generated.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not generate report.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleCreateAIInterpretation() {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const result = await createAIReadinessInterpretation(accessToken, profile.id, jobResult?.id ?? null);
      setAiInterpretationResult(result);
      setMessage(result.cached ? "AI interpretation loaded from cache." : "AI interpretation generated.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not generate AI interpretation.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleCreateRewriteSuggestions() {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const result = await createResumeRewriteSuggestions(accessToken, profile.id, jobResult?.id ?? null);
      setRewriteResult(result);
      setMessage(result.cached ? "Rewrite suggestions loaded from cache." : "Rewrite suggestions generated.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not generate rewrite suggestions.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleRunDashboard() {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const result = await runReadinessDashboard(accessToken, profile.id, jobResult?.id ?? null);
      setDashboardResult(result);
      setMessage("Readiness dashboard completed.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not run readiness dashboard.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleRunSkillGap() {
    if (!accessToken || !profile || !jobResult?.id) {
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const result = await runSkillGapAnalysis(accessToken, profile.id, jobResult.id);
      setSkillGapResult(result);
      setMessage("Skill gap analysis completed.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not run skill gap analysis.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleRunReadinessScores() {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const [ats, completeness] = await Promise.all([
        runAtsReadinessAnalysis(accessToken, profile.id),
        runProfileCompletenessAnalysis(accessToken, profile.id),
      ]);
      setAtsResult(ats);
      setCompletenessResult(completeness);
      setMessage("Readiness scores completed.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not run readiness scores.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleRunAnalysis() {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const result = await runResumeQualityAnalysis(accessToken, profile.id);
      setQualityResult(result);
      setMessage("Resume quality analysis completed.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not run resume analysis.");
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <section className="mt-8 max-w-2xl border border-border bg-white p-5">
      <h2 className="text-base font-semibold">Candidate profile</h2>
      {!accessToken ? (
        <p className="mt-2 text-sm text-muted-foreground">Sign in to create a profile and upload a resume.</p>
      ) : (
        <>
          <form className="mt-4 grid gap-4 sm:grid-cols-2" onSubmit={form.handleSubmit(handleCreateProfile)}>
            <label className="block text-sm font-medium">
              Career goal
              <input className="mt-1 w-full border border-border px-3 py-2" {...form.register("career_goal")} />
            </label>
            <label className="block text-sm font-medium">
              Preferred role
              <input className="mt-1 w-full border border-border px-3 py-2" placeholder="QA Automation Engineer" {...form.register("preferred_role")} />
            </label>
            <button className="inline-flex items-center justify-center gap-2 bg-foreground px-4 py-2 text-sm font-medium text-background sm:col-span-2" disabled={isBusy} type="submit">
              <Plus aria-hidden="true" className="h-4 w-4" />
              Create profile
            </button>
          </form>
          {form.formState.errors.career_goal ? <p className="mt-2 text-sm text-red-600">{form.formState.errors.career_goal.message}</p> : null}
          {form.formState.errors.preferred_role ? <p className="mt-2 text-sm text-red-600">{form.formState.errors.preferred_role.message}</p> : null}
          {profile ? (
            <div className="mt-5 border-t border-border pt-5">
              <p className="text-sm text-muted-foreground">Profile ready for {profile.preferred_role}.</p>
              <label className="mt-4 inline-flex cursor-pointer items-center gap-2 bg-primary px-4 py-2 text-sm font-medium text-primary-foreground">
                <FileUp aria-hidden="true" className="h-4 w-4" />
                Upload resume
                <input className="sr-only" type="file" accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" onChange={handleUpload} />
              </label>
              <button className="ml-3 mt-4 inline-flex items-center justify-center gap-2 border border-red-200 px-4 py-2 text-sm font-medium text-red-700" disabled={isBusy} type="button" onClick={handleDeleteProfile}>
                <Trash2 aria-hidden="true" className="h-4 w-4" />
                Delete profile data
              </button>
            </div>
          ) : null}
          {profile ? (
            <form className="mt-5 border-t border-border pt-5" onSubmit={githubForm.handleSubmit(handleAddGitHub)}>
              <h3 className="text-base font-semibold">Optional GitHub source</h3>
              <div className="mt-3 flex flex-col gap-3 sm:flex-row">
                <input className="w-full border border-border px-3 py-2 text-sm" placeholder="octocat or https://github.com/octocat" {...githubForm.register("username_or_url")} />
                <button className="inline-flex items-center justify-center gap-2 bg-foreground px-4 py-2 text-sm font-medium text-background" disabled={isBusy} type="submit">
                  <Github aria-hidden="true" className="h-4 w-4" />
                  Analyze GitHub
                </button>
              </div>
              {githubForm.formState.errors.username_or_url ? <p className="mt-2 text-sm text-red-600">{githubForm.formState.errors.username_or_url.message}</p> : null}
            </form>
          ) : null}
          {githubResult ? (
            <div className="mt-5 border-t border-border pt-5 text-sm">
              <h3 className="text-base font-semibold">GitHub analysis</h3>
              <dl className="mt-3 grid gap-3 sm:grid-cols-2">
                <JobField label="Username" values={[githubResult.username]} />
                <JobField label="Languages" values={githubResult.primary_languages} />
                <JobField label="Repositories" values={[String(githubResult.analyzed_repository_count)]} />
                <JobField label="README signals" values={[String(githubResult.readme_repository_count)]} />
                <JobField label="Test signals" values={[String(githubResult.test_signal_count)]} />
                <JobField label="CI signals" values={[String(githubResult.ci_signal_count)]} />
                <JobField label="Notable repositories" values={githubResult.notable_repositories.slice(0, 4)} />
              </dl>
            </div>
          ) : null}
          {profile ? (
            <form className="mt-5 border-t border-border pt-5" onSubmit={portfolioForm.handleSubmit(handleAddPortfolio)}>
              <h3 className="text-base font-semibold">Optional portfolio source</h3>
              <div className="mt-3 flex flex-col gap-3 sm:flex-row">
                <input className="w-full border border-border px-3 py-2 text-sm" placeholder="https://your-portfolio.com" {...portfolioForm.register("url")} />
                <button className="inline-flex items-center justify-center gap-2 bg-foreground px-4 py-2 text-sm font-medium text-background" disabled={isBusy} type="submit">
                  <LinkIcon aria-hidden="true" className="h-4 w-4" />
                  Analyze portfolio
                </button>
              </div>
              {portfolioForm.formState.errors.url ? <p className="mt-2 text-sm text-red-600">{portfolioForm.formState.errors.url.message}</p> : null}
            </form>
          ) : null}
          {portfolioResult ? (
            <div className="mt-5 border-t border-border pt-5 text-sm">
              <h3 className="text-base font-semibold">Portfolio analysis</h3>
              <dl className="mt-3 grid gap-3 sm:grid-cols-2">
                <JobField label="Title" values={portfolioResult.title ? [portfolioResult.title] : []} />
                <JobField label="Technical signals" values={portfolioResult.technical_signals} />
                <JobField label="Non-technical signals" values={portfolioResult.non_technical_signals} />
                <JobField label="Project signals" values={[String(portfolioResult.project_signal_count)]} />
                <JobField label="Contact signals" values={[String(portfolioResult.contact_signal_count)]} />
                <JobField label="Evidence records" values={[String(portfolioResult.evidence_count)]} />
              </dl>
            </div>
          ) : null}
          {profile ? (
            <form className="mt-5 border-t border-border pt-5" onSubmit={linkedInForm.handleSubmit(handleAddLinkedInText)}>
              <h3 className="text-base font-semibold">Optional LinkedIn source</h3>
              <textarea className="mt-3 min-h-32 w-full border border-border px-3 py-2 text-sm" placeholder="Paste LinkedIn profile text or export content. Direct LinkedIn scraping is not supported." {...linkedInForm.register("text")} />
              {linkedInForm.formState.errors.text ? <p className="mt-2 text-sm text-red-600">{linkedInForm.formState.errors.text.message}</p> : null}
              <div className="mt-3 flex flex-col gap-3 sm:flex-row">
                <button className="inline-flex items-center justify-center gap-2 bg-foreground px-4 py-2 text-sm font-medium text-background" disabled={isBusy} type="submit">
                  <Linkedin aria-hidden="true" className="h-4 w-4" />
                  Analyze pasted text
                </button>
                <label className="inline-flex cursor-pointer items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium">
                  <FileUp aria-hidden="true" className="h-4 w-4" />
                  Upload PDF/DOCX
                  <input className="sr-only" type="file" accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" onChange={handleUploadLinkedIn} />
                </label>
              </div>
            </form>
          ) : null}
          {linkedInResult ? (
            <div className="mt-5 border-t border-border pt-5 text-sm">
              <h3 className="text-base font-semibold">LinkedIn analysis</h3>
              <dl className="mt-3 grid gap-3 sm:grid-cols-2">
                <JobField label="Headline" values={linkedInResult.headline ? [linkedInResult.headline] : []} />
                <JobField label="Source type" values={[linkedInResult.source_type]} />
                <JobField label="Skill signals" values={linkedInResult.skill_signals} />
                <JobField label="Experience items" values={[String(linkedInResult.experience_count)]} />
                <JobField label="Evidence records" values={[String(linkedInResult.evidence_count)]} />
                <JobField label="Profile version" values={[String(linkedInResult.profile_version ?? "Pending")]} />
              </dl>
            </div>
          ) : null}
          {uploadResult ? (
            <dl className="mt-5 grid gap-3 border-t border-border pt-5 text-sm sm:grid-cols-2">
              <div>
                <dt className="font-medium">File</dt>
                <dd className="text-muted-foreground">{uploadResult.original_filename}</dd>
              </div>
              <div>
                <dt className="font-medium">Status</dt>
                <dd className="text-muted-foreground">{uploadResult.status}</dd>
              </div>
              <div>
                <dt className="font-medium">Source type</dt>
                <dd className="text-muted-foreground">{uploadResult.source_type}</dd>
              </div>
              <div>
                <dt className="font-medium">Text length</dt>
                <dd className="text-muted-foreground">{uploadResult.text_length}</dd>
              </div>
              <div>
                <dt className="font-medium">Evidence records</dt>
                <dd className="text-muted-foreground">{uploadResult.evidence_count}</dd>
              </div>
              <div>
                <dt className="font-medium">Profile version</dt>
                <dd className="text-muted-foreground">{uploadResult.profile_version ?? "Pending"}</dd>
              </div>
              <button className="inline-flex items-center justify-center gap-2 bg-foreground px-4 py-2 text-sm font-medium text-background sm:col-span-2" disabled={isBusy} type="button" onClick={handleRunAnalysis}>
                <Gauge aria-hidden="true" className="h-4 w-4" />
                Run resume quality analysis
              </button>
              <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium sm:col-span-2" disabled={isBusy} type="button" onClick={handleRunReadinessScores}>
                <ClipboardCheck aria-hidden="true" className="h-4 w-4" />
                Run readiness scores
              </button>
              <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium sm:col-span-2" disabled={isBusy} type="button" onClick={handleRunDashboard}>
                <LayoutDashboard aria-hidden="true" className="h-4 w-4" />
                Run readiness dashboard
              </button>
              <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium sm:col-span-2" disabled={isBusy} type="button" onClick={handleCreateReport}>
                <ScrollText aria-hidden="true" className="h-4 w-4" />
                Generate basic report
              </button>
              <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium sm:col-span-2" disabled={isBusy} type="button" onClick={handleCreateAIInterpretation}>
                <Sparkles aria-hidden="true" className="h-4 w-4" />
                Generate AI interpretation
              </button>
              <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium sm:col-span-2" disabled={isBusy} type="button" onClick={handleCreateRewriteSuggestions}>
                <ScrollText aria-hidden="true" className="h-4 w-4" />
                Generate rewrite suggestions
              </button>
            </dl>
          ) : null}
          {qualityResult ? (
            <div className="mt-5 border-t border-border pt-5 text-sm">
              <div className="flex items-baseline gap-3">
                <h3 className="text-base font-semibold">Resume quality</h3>
                <p className="text-2xl font-semibold">{qualityResult.score}</p>
              </div>
              {qualityResult.findings.length ? (
                <ul className="mt-4 space-y-3">
                  {qualityResult.findings.slice(0, 4).map((finding) => (
                    <li key={finding.code} className="border border-border p-3">
                      <p className="font-medium">{finding.title}</p>
                      <p className="mt-1 text-muted-foreground">{finding.recommendation}</p>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-2 text-muted-foreground">No major resume quality issues found.</p>
              )}
            </div>
          ) : null}
          {atsResult || completenessResult ? (
            <div className="mt-5 border-t border-border pt-5 text-sm">
              <h3 className="text-base font-semibold">Readiness scores</h3>
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                {atsResult ? <ScoreCard title="Snipe ATS Readiness" result={atsResult} /> : null}
                {completenessResult ? <ScoreCard title="Profile Completeness" result={completenessResult} /> : null}
              </div>
            </div>
          ) : null}
          {profile ? (
            <form className="mt-5 border-t border-border pt-5" onSubmit={jobForm.handleSubmit(handleCreateJobDescription)}>
              <h3 className="text-base font-semibold">Target job description</h3>
              <textarea className="mt-3 min-h-36 w-full border border-border px-3 py-2 text-sm" placeholder="Paste a target job description here." {...jobForm.register("text")} />
              {jobForm.formState.errors.text ? <p className="mt-2 text-sm text-red-600">{jobForm.formState.errors.text.message}</p> : null}
              <button className="mt-3 inline-flex items-center justify-center gap-2 bg-foreground px-4 py-2 text-sm font-medium text-background" disabled={isBusy} type="submit">
                <BriefcaseBusiness aria-hidden="true" className="h-4 w-4" />
                Analyze job description
              </button>
            </form>
          ) : null}
          {jobResult ? (
            <div className="mt-5 border-t border-border pt-5 text-sm">
              <h3 className="text-base font-semibold">{jobResult.structured.title ?? "Target role"}</h3>
              <dl className="mt-3 grid gap-3 sm:grid-cols-2">
                <JobField label="Company" values={jobResult.structured.company ? [jobResult.structured.company] : []} />
                <JobField label="Seniority" values={jobResult.structured.seniority ? [jobResult.structured.seniority] : []} />
                <JobField label="Required skills" values={jobResult.structured.required_skills} />
                <JobField label="Preferred skills" values={jobResult.structured.preferred_skills} />
                <JobField label="Tools" values={jobResult.structured.tools} />
                <JobField label="ATS keywords" values={jobResult.structured.ats_keywords.slice(0, 8)} />
              </dl>
              <button className="mt-4 inline-flex items-center justify-center gap-2 bg-foreground px-4 py-2 text-sm font-medium text-background" disabled={isBusy || !uploadResult} type="button" onClick={handleRunSkillGap}>
                <GitCompareArrows aria-hidden="true" className="h-4 w-4" />
                Run skill gap analysis
              </button>
            </div>
          ) : null}
          {skillGapResult ? (
            <div className="mt-5 border-t border-border pt-5 text-sm">
              <div className="flex items-baseline gap-3">
                <h3 className="text-base font-semibold">Skill gap</h3>
                <p className="text-2xl font-semibold">{skillGapResult.score}</p>
              </div>
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                <JobField label="Matched" values={skillGapResult.matched_skills.map((item) => item.skill)} />
                <JobField label="Missing" values={skillGapResult.missing_skills.map((item) => item.skill).slice(0, 8)} />
                <JobField label="Transferable" values={skillGapResult.transferable_skills.map((item) => item.skill)} />
                <JobField label="Not relevant" values={skillGapResult.not_relevant_skills.map((item) => item.skill).slice(0, 8)} />
              </div>
            </div>
          ) : null}
          {dashboardResult ? (
            <div className="mt-5 border-t border-border pt-5 text-sm">
              <div className="flex items-baseline gap-3">
                <h3 className="text-base font-semibold">Readiness dashboard</h3>
                <p className="text-2xl font-semibold">{dashboardResult.scores.overall}</p>
              </div>
              <dl className="mt-3 grid gap-3 sm:grid-cols-2">
                <JobField label="Resume quality" values={[String(dashboardResult.scores.resume_quality)]} />
                <JobField label="ATS readiness" values={[String(dashboardResult.scores.ats_readiness)]} />
                <JobField label="Profile completeness" values={[String(dashboardResult.scores.profile_completeness)]} />
                <JobField label="Skill alignment" values={dashboardResult.scores.skill_alignment === null ? [] : [String(dashboardResult.scores.skill_alignment)]} />
                <JobField label="Primary specialization" values={dashboardResult.interpretation.primary_specialization ? [dashboardResult.interpretation.primary_specialization.name] : []} />
                <JobField label="Estimated seniority" values={dashboardResult.interpretation.estimated_seniority ? [dashboardResult.interpretation.estimated_seniority] : []} />
              </dl>
            </div>
          ) : null}
          {reportResult ? (
            <div className="mt-5 border-t border-border pt-5 text-sm">
              <div className="flex items-baseline gap-3">
                <h3 className="text-base font-semibold">{reportResult.title}</h3>
                <p className="text-2xl font-semibold">{reportResult.readiness.scores.overall}</p>
              </div>
              <p className="mt-2 text-muted-foreground">{reportResult.summary}</p>
              <dl className="mt-3 grid gap-3 sm:grid-cols-2">
                <JobField label="Strengths" values={reportResult.strengths.slice(0, 3)} />
                <JobField label="Improvement areas" values={reportResult.weaknesses.slice(0, 3)} />
                <JobField label="Skill gaps" values={reportResult.skill_gaps.slice(0, 6)} />
              </dl>
              <pre className="mt-4 max-h-72 overflow-auto whitespace-pre-wrap border border-border bg-muted p-3 text-xs text-muted-foreground">
                {reportResult.markdown}
              </pre>
            </div>
          ) : null}
          {aiInterpretationResult ? (
            <div className="mt-5 border-t border-border pt-5 text-sm">
              <div className="flex items-baseline gap-3">
                <h3 className="text-base font-semibold">AI interpretation</h3>
                <p className="text-xs text-muted-foreground">
                  {aiInterpretationResult.cached ? "Cached" : aiInterpretationResult.provider}
                </p>
              </div>
              <p className="mt-2 text-muted-foreground">{aiInterpretationResult.summary}</p>
              <p className="mt-3 text-muted-foreground">{aiInterpretationResult.readiness_explanation}</p>
              <div className="mt-4 grid gap-3">
                {aiInterpretationResult.recommendations.map((item) => (
                  <div key={`${item.priority}-${item.title}`} className="border border-border p-3">
                    <p className="font-medium">{item.title}</p>
                    <p className="mt-1 text-muted-foreground">{item.rationale}</p>
                    <p className="mt-2">{item.action}</p>
                  </div>
                ))}
              </div>
              {aiInterpretationResult.cautions.length ? (
                <ul className="mt-4 list-disc space-y-1 pl-5 text-muted-foreground">
                  {aiInterpretationResult.cautions.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              ) : null}
            </div>
          ) : null}
          {rewriteResult ? (
            <div className="mt-5 border-t border-border pt-5 text-sm">
              <div className="flex items-baseline gap-3">
                <h3 className="text-base font-semibold">Rewrite suggestions</h3>
                <p className="text-xs text-muted-foreground">
                  {rewriteResult.cached ? "Cached" : rewriteResult.provider}
                </p>
              </div>
              <p className="mt-2 text-muted-foreground">{rewriteResult.summary}</p>
              <div className="mt-4 grid gap-3">
                {rewriteResult.suggestions.map((item) => (
                  <div key={`${item.original}-${item.suggested}`} className="border border-border p-3">
                    <p className="font-medium">Original</p>
                    <p className="mt-1 text-muted-foreground">{item.original}</p>
                    <p className="mt-3 font-medium">Suggested</p>
                    <p className="mt-1">{item.suggested}</p>
                    <p className="mt-3 text-muted-foreground">{item.rationale}</p>
                    <JobField label="Evidence used" values={item.evidence_used} />
                    {item.needs_candidate_value ? (
                      <p className="mt-2 text-muted-foreground">Candidate review required before use.</p>
                    ) : null}
                  </div>
                ))}
              </div>
              {rewriteResult.cautions.length ? (
                <ul className="mt-4 list-disc space-y-1 pl-5 text-muted-foreground">
                  {rewriteResult.cautions.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              ) : null}
            </div>
          ) : null}
        </>
      )}
      {message ? <p className="mt-4 text-sm text-muted-foreground">{message}</p> : null}
    </section>
  );
}

function JobField({ label, values }: { label: string; values: string[] }) {
  return (
    <div>
      <dt className="font-medium">{label}</dt>
      <dd className="mt-1 text-muted-foreground">{values.length ? values.join(", ") : "Not found"}</dd>
    </div>
  );
}

function ScoreCard({ title, result }: { title: string; result: DeterministicScoreResult }) {
  const topFinding = result.findings[0];

  return (
    <div className="border border-border p-3">
      <p className="font-medium">{title}</p>
      <p className="mt-2 text-2xl font-semibold">{result.score}</p>
      {topFinding ? (
        <p className="mt-2 text-muted-foreground">{topFinding.recommendation}</p>
      ) : (
        <p className="mt-2 text-muted-foreground">No major readiness issues found.</p>
      )}
    </div>
  );
}
