import { BriefcaseBusiness } from "lucide-react";
import { UseFormReturn } from "react-hook-form";

import { JobDescriptionValues } from "@/features/resume/resumeWorkflowForms";
import { JobDescriptionResult } from "@/lib/api";

type TargetJobFormProps = {
  isVisible: boolean;
  isBusy: boolean;
  jobForm: UseFormReturn<JobDescriptionValues>;
  jobOptions: JobDescriptionResult[];
  matchLimit: number;
  matchQuery: string;
  selectedJobId: string | null;
  onCreateJobDescription: (values: JobDescriptionValues) => void;
  onMatchLimitChange: (value: number) => void;
  onMatchQueryChange: (value: string) => void;
  onRunJobMatches: () => void;
  onSelectJobDescription: (jobId: string) => void;
};

export function TargetJobForm({
  isVisible,
  isBusy,
  jobForm,
  jobOptions,
  matchLimit,
  matchQuery,
  selectedJobId,
  onCreateJobDescription,
  onMatchLimitChange,
  onMatchQueryChange,
  onRunJobMatches,
  onSelectJobDescription,
}: TargetJobFormProps) {
  if (!isVisible) {
    return null;
  }

  return (
    <form className="mt-5 border-t border-border pt-5" onSubmit={jobForm.handleSubmit(onCreateJobDescription)}>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-baseline sm:justify-between">
        <h3 className="text-base font-semibold">Target job description</h3>
        {selectedJobId ? <p className="text-xs text-muted-foreground">Active target selected</p> : null}
      </div>
      {jobOptions.length ? (
        <label className="mt-3 block text-sm font-medium">
          Saved target jobs
          <select
            className="mt-2 w-full border border-border bg-background px-3 py-2 text-sm"
            disabled={isBusy}
            value={selectedJobId ?? ""}
            onChange={(event) => onSelectJobDescription(event.target.value)}
          >
            <option value="">Select a saved target job</option>
            {jobOptions.map((job) => (
              <option key={job.id ?? job.input_hash} value={job.id ?? ""}>
                {job.structured.title ?? "Untitled role"}
                {job.structured.company ? ` at ${job.structured.company}` : ""}
              </option>
            ))}
          </select>
        </label>
      ) : null}
      <textarea className="mt-3 min-h-36 w-full border border-border px-3 py-2 text-sm" placeholder="Paste a target job description here." {...jobForm.register("text")} />
      {jobForm.formState.errors.text ? <p className="mt-2 text-sm text-red-600">{jobForm.formState.errors.text.message}</p> : null}
      <button className="mt-3 inline-flex items-center justify-center gap-2 bg-foreground px-4 py-2 text-sm font-medium text-background" disabled={isBusy} type="submit">
        <BriefcaseBusiness aria-hidden="true" className="h-4 w-4" />
        Analyze job description
      </button>
      <div className="mt-5 border-t border-border pt-5">
        <h4 className="text-sm font-semibold">Job match search</h4>
        <div className="mt-3 grid gap-3 sm:grid-cols-[1fr_9rem]">
          <label className="block text-sm font-medium">
            Search query
            <input
              className="mt-2 w-full border border-border bg-background px-3 py-2 text-sm"
              disabled={isBusy}
              placeholder="Role, skills, location, or industry"
              type="text"
              value={matchQuery}
              onChange={(event) => onMatchQueryChange(event.target.value)}
            />
          </label>
          <label className="block text-sm font-medium">
            Results
            <select
              className="mt-2 w-full border border-border bg-background px-3 py-2 text-sm"
              disabled={isBusy}
              value={String(matchLimit)}
              onChange={(event) => onMatchLimitChange(Number(event.target.value))}
            >
              <option value="5">5</option>
              <option value="10">10</option>
              <option value="15">15</option>
              <option value="20">20</option>
            </select>
          </label>
        </div>
        <button className="mt-3 inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={onRunJobMatches}>
          <BriefcaseBusiness aria-hidden="true" className="h-4 w-4" />
          Run job match search
        </button>
      </div>
    </form>
  );
}
