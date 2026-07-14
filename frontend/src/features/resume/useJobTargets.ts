import { ChangeEvent, useState } from "react";

import { JobDescriptionValues } from "@/features/resume/resumeWorkflowForms";
import {
  ApplicationMaterialsResult,
  CandidateProfile,
  InterviewPrepResult,
  JobDescriptionResult,
  JobMatch,
  JobMatchResult,
  ResumeTailoringPackageResult,
  SavedJobMatchRun,
  createApplicationMaterials,
  createInterviewPrep,
  createJobDescription,
  createResumeTailoringPackage,
  getSavedJobMatch,
  listJobDescriptions,
  listSavedJobMatches,
  runJobMatches,
  uploadJobDescription,
} from "@/lib/api";

type GenerateFromMatchType = "tailoring" | "interview" | "materials";

type UseJobTargetsParams = {
  accessToken: string | null;
  profile: CandidateProfile | null;
  onBusyChange: (isBusy: boolean) => void;
  onBusyLabelChange: (label: string | null) => void;
  onMessage: (message: string | null) => void;
  onResetTargetDependentResults: (options?: {
    clearGeneratedOutputs?: boolean;
    clearJobMatches?: boolean;
  }) => void;
  onApplicationMaterialsResult: (result: ApplicationMaterialsResult) => void;
  onInterviewResult: (result: InterviewPrepResult) => void;
  onTailoringResult: (result: ResumeTailoringPackageResult) => void;
  refreshGeneratedOutputs: (token: string, profileId: string) => Promise<void>;
};

export function useJobTargets({
  accessToken,
  profile,
  onBusyChange,
  onBusyLabelChange,
  onMessage,
  onResetTargetDependentResults,
  onApplicationMaterialsResult,
  onInterviewResult,
  onTailoringResult,
  refreshGeneratedOutputs,
}: UseJobTargetsParams) {
  const [jobResult, setJobResult] = useState<JobDescriptionResult | null>(null);
  const [jobOptions, setJobOptions] = useState<JobDescriptionResult[]>([]);
  const [jobMatchResult, setJobMatchResult] = useState<JobMatchResult | null>(null);
  const [savedJobMatches, setSavedJobMatches] = useState<SavedJobMatchRun[]>([]);
  const [jobMatchTargetIds, setJobMatchTargetIds] = useState<Record<string, string>>({});
  const [isJobMatchHistoryLoading, setIsJobMatchHistoryLoading] = useState(false);
  const [jobMatchQuery, setJobMatchQuery] = useState("");
  const [jobMatchLimit, setJobMatchLimit] = useState(10);

  function clearJobTargetState() {
    setJobResult(null);
    setJobOptions([]);
    setJobMatchResult(null);
    setSavedJobMatches([]);
    setJobMatchTargetIds({});
    setJobMatchQuery("");
    setJobMatchLimit(10);
  }

  function clearJobMatchResult() {
    setJobMatchResult(null);
  }

  function setLoadedJobDescriptions(jobs: JobDescriptionResult[]) {
    setJobOptions(jobs);
  }

  async function loadJobDescriptionsForProfile(token: string, profileId: string) {
    const jobs = await listJobDescriptions(token, profileId);
    setLoadedJobDescriptions(jobs);
    return jobs;
  }

  async function handleCreateJobDescription(values: JobDescriptionValues) {
    if (!accessToken || !profile) {
      return;
    }

    onBusyChange(true);
    onMessage(null);
    try {
      const result = await createJobDescription(accessToken, profile.id, values.text);
      setJobResult(result);
      setJobOptions((current) => [result, ...current.filter((job) => job.id !== result.id)]);
      onResetTargetDependentResults({ clearGeneratedOutputs: true, clearJobMatches: true });
      onMessage("Job description analyzed.");
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not analyze job description.");
    } finally {
      onBusyChange(false);
    }
  }

  async function handleUploadJobDescription(event: ChangeEvent<HTMLInputElement>) {
    if (!accessToken || !profile) {
      return;
    }
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) {
      return;
    }

    onBusyChange(true);
    onMessage(null);
    try {
      const result = await uploadJobDescription(accessToken, profile.id, file);
      setJobResult(result);
      setJobOptions((current) => [result, ...current.filter((job) => job.id !== result.id)]);
      onResetTargetDependentResults({ clearGeneratedOutputs: true, clearJobMatches: true });
      onMessage("Job description upload analyzed.");
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not upload job description.");
    } finally {
      onBusyChange(false);
    }
  }

  function handleSelectJobDescription(jobId: string) {
    const selected = jobOptions.find((job) => job.id === jobId) ?? null;
    setJobResult(selected);
    onResetTargetDependentResults();
    onMessage(selected ? "Saved target job selected." : "Target job selection cleared.");
  }

  async function saveJobMatchAsTarget(match: JobMatch) {
    if (!accessToken || !profile) {
      return null;
    }

    const existingTargetId = jobMatchTargetIds[match.job_reference_id];
    if (existingTargetId && jobResult?.id === existingTargetId) {
      return jobResult;
    }

    const existingTarget = existingTargetId
      ? jobOptions.find((job) => job.id === existingTargetId) ?? null
      : null;
    if (existingTarget) {
      setJobResult(existingTarget);
      onResetTargetDependentResults();
      return existingTarget;
    }

    if (match.source_excerpt.trim().length < 100) {
      onMessage("This job match does not include enough source text to save as a target job.");
      return null;
    }

    const result = await createJobDescription(accessToken, profile.id, match.source_excerpt);
    setJobResult(result);
    setJobOptions((current) => [result, ...current.filter((job) => job.id !== result.id)]);
    if (result.id) {
      setJobMatchTargetIds((current) => ({
        ...current,
        [match.job_reference_id]: result.id ?? "",
      }));
    }
    onResetTargetDependentResults();
    return result;
  }

  async function handleSaveJobMatchAsTarget(match: JobMatch) {
    if (!accessToken || !profile) {
      return;
    }

    onBusyChange(true);
    onMessage(null);
    try {
      const result = await saveJobMatchAsTarget(match);
      if (result) {
        onMessage("Job match saved as the active target job.");
      }
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not save job match as target.");
    } finally {
      onBusyChange(false);
    }
  }

  async function handleSaveJobMatchAndGenerate(match: JobMatch, outputType: GenerateFromMatchType) {
    if (!accessToken || !profile) {
      return;
    }

    const labels = {
      tailoring: "tailoring package",
      interview: "interview prep",
      materials: "application materials",
    };
    onBusyChange(true);
    onBusyLabelChange(`Saving match and generating ${labels[outputType]}...`);
    onMessage(null);
    try {
      const targetJob = await saveJobMatchAsTarget(match);
      if (!targetJob?.id) {
        return;
      }
      if (outputType === "tailoring") {
        const result = await createResumeTailoringPackage(accessToken, profile.id, targetJob.id, false);
        onTailoringResult(result);
      } else if (outputType === "interview") {
        const result = await createInterviewPrep(accessToken, profile.id, targetJob.id, false);
        onInterviewResult(result);
      } else {
        const result = await createApplicationMaterials(accessToken, profile.id, targetJob.id, false);
        onApplicationMaterialsResult(result);
      }
      await refreshGeneratedOutputs(accessToken, profile.id);
      onMessage(`Job match saved and ${labels[outputType]} generated.`);
    } catch (error) {
      onMessage(error instanceof Error ? error.message : `Could not generate ${labels[outputType]}.`);
    } finally {
      onBusyChange(false);
      onBusyLabelChange(null);
    }
  }

  async function handleRunJobMatches() {
    if (!accessToken || !profile) {
      return;
    }

    onBusyChange(true);
    onBusyLabelChange("Retrieving and ranking job matches...");
    onMessage(null);
    try {
      const result = await runJobMatches(
        accessToken,
        profile.id,
        jobMatchQuery.trim() || profile.preferred_role,
        jobMatchLimit,
      );
      setJobMatchResult(result);
      const savedRuns = await listSavedJobMatches(accessToken, profile.id);
      setSavedJobMatches(savedRuns);
      onMessage(result.matches.length ? "Job matches ranked." : "No job references found yet.");
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not retrieve job matches.");
    } finally {
      onBusyChange(false);
      onBusyLabelChange(null);
    }
  }

  async function handleLoadJobMatchHistory() {
    if (!accessToken || !profile) {
      return;
    }

    setIsJobMatchHistoryLoading(true);
    onMessage(null);
    try {
      const runs = await listSavedJobMatches(accessToken, profile.id);
      setSavedJobMatches(runs);
      onMessage(runs.length ? "Job match history loaded." : "No saved job matches found yet.");
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not load job match history.");
    } finally {
      setIsJobMatchHistoryLoading(false);
    }
  }

  async function handleOpenSavedJobMatch(analysisId: string) {
    if (!accessToken || !profile) {
      return;
    }

    setIsJobMatchHistoryLoading(true);
    onMessage(null);
    try {
      const run = await getSavedJobMatch(accessToken, profile.id, analysisId);
      setJobMatchResult(run.result);
      setJobMatchQuery(run.query);
      setSavedJobMatches((current) => [
        run,
        ...current.filter((item) => item.id !== run.id),
      ]);
      onMessage("Saved job match opened.");
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not open saved job match.");
    } finally {
      setIsJobMatchHistoryLoading(false);
    }
  }

  return {
    clearJobMatchResult,
    clearJobTargetState,
    handleCreateJobDescription,
    handleLoadJobMatchHistory,
    handleOpenSavedJobMatch,
    handleRunJobMatches,
    handleSaveJobMatchAndGenerate,
    handleSaveJobMatchAsTarget,
    handleSelectJobDescription,
    handleUploadJobDescription,
    isJobMatchHistoryLoading,
    jobMatchLimit,
    jobMatchQuery,
    jobMatchResult,
    jobMatchTargetIds,
    jobOptions,
    jobResult,
    loadJobDescriptionsForProfile,
    savedJobMatches,
    setJobMatchLimit,
    setJobMatchQuery,
    setJobResult,
    setLoadedJobDescriptions,
  };
}
