import { GeneratedOutput, JobDescriptionResult } from "@/lib/api";

type UseResumeWorkflowDerivedStateArgs = {
  generatedOutputFilter: string;
  generatedOutputs: GeneratedOutput[];
  jobResult: JobDescriptionResult | null;
};

export function useResumeWorkflowDerivedState({
  generatedOutputFilter,
  generatedOutputs,
  jobResult,
}: UseResumeWorkflowDerivedStateArgs) {
  const activeTargetLabel = jobResult
    ? `${jobResult.structured.title ?? "Target role"}${jobResult.structured.company ? ` at ${jobResult.structured.company}` : ""}`
    : null;

  const filteredGeneratedOutputs =
    generatedOutputFilter === "all"
      ? generatedOutputs
      : generatedOutputFilter === "active_target"
        ? generatedOutputs.filter((item) => Boolean(jobResult?.id) && item.job_description_id === jobResult?.id)
        : generatedOutputs.filter((item) => item.output_type === generatedOutputFilter);

  return {
    activeTargetLabel,
    filteredGeneratedOutputs,
  };
}
