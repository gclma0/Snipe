import { BriefcaseBusiness } from "lucide-react";
import { UseFormReturn } from "react-hook-form";

import { JobDescriptionValues } from "@/features/resume/resumeWorkflowForms";

type TargetJobFormProps = {
  isVisible: boolean;
  isBusy: boolean;
  jobForm: UseFormReturn<JobDescriptionValues>;
  onCreateJobDescription: (values: JobDescriptionValues) => void;
};

export function TargetJobForm({
  isVisible,
  isBusy,
  jobForm,
  onCreateJobDescription,
}: TargetJobFormProps) {
  if (!isVisible) {
    return null;
  }

  return (
    <form className="mt-5 border-t border-border pt-5" onSubmit={jobForm.handleSubmit(onCreateJobDescription)}>
      <h3 className="text-base font-semibold">Target job description</h3>
      <textarea className="mt-3 min-h-36 w-full border border-border px-3 py-2 text-sm" placeholder="Paste a target job description here." {...jobForm.register("text")} />
      {jobForm.formState.errors.text ? <p className="mt-2 text-sm text-red-600">{jobForm.formState.errors.text.message}</p> : null}
      <button className="mt-3 inline-flex items-center justify-center gap-2 bg-foreground px-4 py-2 text-sm font-medium text-background" disabled={isBusy} type="submit">
        <BriefcaseBusiness aria-hidden="true" className="h-4 w-4" />
        Analyze job description
      </button>
    </form>
  );
}
