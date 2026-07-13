import { Download, GitCompareArrows } from "lucide-react";

import { formatApplyRecommendation } from "@/features/resume/generatedOutputFormatting";
import { JobField, ScoreCard } from "@/features/resume/resumeDisplay";
import {
  BasicReportResult,
  DeterministicScoreResult,
  FullCareerReportResult,
  JobDescriptionResult,
  JobMatchResult,
  ReadinessDashboardResult,
  ResumeQualityResult,
  SkillGapResult,
} from "@/lib/api";

type ReadinessResultsProps = {
  qualityResult: ResumeQualityResult | null;
  atsResult: DeterministicScoreResult | null;
  completenessResult: DeterministicScoreResult | null;
};

export function ReadinessResults({
  qualityResult,
  atsResult,
  completenessResult,
}: ReadinessResultsProps) {
  return (
    <>
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
    </>
  );
}

type JobAnalysisResultsProps = {
  jobResult: JobDescriptionResult | null;
  skillGapResult: SkillGapResult | null;
  dashboardResult: ReadinessDashboardResult | null;
  jobMatchResult: JobMatchResult | null;
  isBusy: boolean;
  hasUploadResult: boolean;
  onRunSkillGap: () => void;
};

export function JobAnalysisResults({
  jobResult,
  skillGapResult,
  dashboardResult,
  jobMatchResult,
  isBusy,
  hasUploadResult,
  onRunSkillGap,
}: JobAnalysisResultsProps) {
  return (
    <>
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
          <button className="mt-4 inline-flex items-center justify-center gap-2 bg-foreground px-4 py-2 text-sm font-medium text-background" disabled={isBusy || !hasUploadResult} type="button" onClick={onRunSkillGap}>
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
      {jobMatchResult ? (
        <div className="mt-5 border-t border-border pt-5 text-sm">
          <div className="flex items-baseline gap-3">
            <h3 className="text-base font-semibold">Job matches</h3>
            <p className="text-xs text-muted-foreground">{jobMatchResult.match_count} ranked</p>
          </div>
          <div className="mt-4 grid gap-3">
            {jobMatchResult.matches.map((item) => (
              <div key={`${item.job_reference_id}-${item.citation.chunk_id ?? "chunk"}`} className="border border-border p-3">
                <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between">
                  <p className="font-medium">{item.title}</p>
                  <p className="text-2xl font-semibold">{item.match_score}</p>
                </div>
                <p className="mt-2 text-muted-foreground">{item.explanation}</p>
                <dl className="mt-3 grid gap-3 sm:grid-cols-2">
                  <JobField label="Recommendation" values={[formatApplyRecommendation(item.apply_recommendation)]} />
                  <JobField label="Skill alignment" values={[String(item.skill_alignment_score)]} />
                  <JobField label="Matched" values={item.matched_skills.slice(0, 8)} />
                  <JobField label="Missing" values={item.missing_skills.slice(0, 8)} />
                  <JobField label="Relevant experience" values={item.relevant_experience.slice(0, 3)} />
                  <JobField label="Concerns" values={item.concerns.slice(0, 4)} />
                </dl>
                <p className="mt-3 text-xs text-muted-foreground">
                  Source: {item.citation.title}
                  {item.citation.source_url ? ` (${item.citation.source_url})` : ""}
                </p>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </>
  );
}

type ReportResultsProps = {
  reportResult: BasicReportResult | null;
  fullReportResult: FullCareerReportResult | null;
  isBusy: boolean;
  onDownloadFullReport: () => void;
};

export function ReportResults({
  reportResult,
  fullReportResult,
  isBusy,
  onDownloadFullReport,
}: ReportResultsProps) {
  return (
    <>
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
      {fullReportResult ? (
        <div className="mt-5 border-t border-border pt-5 text-sm">
          <div className="flex items-baseline gap-3">
            <h3 className="text-base font-semibold">{fullReportResult.title}</h3>
            <p className="text-xs text-muted-foreground">{fullReportResult.report_version}</p>
          </div>
          <p className="mt-2 text-muted-foreground">{fullReportResult.summary}</p>
          <dl className="mt-3 grid gap-3 sm:grid-cols-2">
            <JobField label="Sections included" values={fullReportResult.sections_included.slice(0, 12)} />
          </dl>
          <button className="mt-4 inline-flex items-center justify-center gap-2 border border-border px-3 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={onDownloadFullReport}>
            <Download aria-hidden="true" className="h-4 w-4" />
            Download full report
          </button>
          <pre className="mt-4 max-h-96 overflow-auto whitespace-pre-wrap border border-border bg-muted p-3 text-xs text-muted-foreground">
            {fullReportResult.markdown}
          </pre>
        </div>
      ) : null}
    </>
  );
}
