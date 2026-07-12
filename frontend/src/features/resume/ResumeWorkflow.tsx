import { zodResolver } from "@hookform/resolvers/zod";
import { BriefcaseBusiness, ClipboardCheck, FileUp, Gauge, GitCompareArrows, Plus } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import {
  CandidateProfile,
  DeterministicScoreResult,
  JobDescriptionResult,
  ResumeQualityResult,
  ResumeUploadResult,
  SkillGapResult,
  createJobDescription,
  createProfile,
  runAtsReadinessAnalysis,
  runProfileCompletenessAnalysis,
  runResumeQualityAnalysis,
  runSkillGapAnalysis,
  uploadResume,
} from "@/lib/api";

const profileSchema = z.object({
  career_goal: z.string().min(1, "Career goal is required.").max(120),
  preferred_role: z.string().min(1, "Preferred role is required.").max(120),
});

const jobDescriptionSchema = z.object({
  text: z.string().min(100, "Paste at least 100 characters from the job description.").max(60000),
});

type ProfileValues = z.infer<typeof profileSchema>;
type JobDescriptionValues = z.infer<typeof jobDescriptionSchema>;

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
  const [skillGapResult, setSkillGapResult] = useState<SkillGapResult | null>(null);
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
      setSkillGapResult(null);
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
      setMessage("Job description analyzed.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not analyze job description.");
    } finally {
      setIsBusy(false);
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
      setSkillGapResult(null);
      setMessage("Resume uploaded and parsed.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not upload resume.");
    } finally {
      setIsBusy(false);
      event.target.value = "";
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
