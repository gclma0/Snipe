import { ResumeActionsPanel } from "@/features/resume/ResumeActionsPanel";
import { ResumeUploadResult } from "@/lib/api";

type ResumeUploadSummaryProps = {
  uploadResult: ResumeUploadResult | null;
  activeTargetLabel: string | null;
  isBusy: boolean;
  isSavedOutputsLoading: boolean;
  onRunAnalysis: () => void;
  onRunReadinessScores: () => void;
  onRunDashboard: () => void;
  onRunJobMatches: () => void;
  onCreateReport: () => void;
  onCreateFullReport: () => void;
  onLoadGeneratedOutputs: () => void;
  onCreateAIInterpretation: (forceRegenerate?: boolean) => void;
  onCreateRewriteSuggestions: (forceRegenerate?: boolean) => void;
  onCreateTailoringPackage: (forceRegenerate?: boolean) => void;
  onCreateInterviewPrep: (forceRegenerate?: boolean) => void;
  onCreateClaimVerification: (forceRegenerate?: boolean) => void;
  onStartMockInterview: () => void;
  onCreateOutreachPack: () => void;
  onCreateCareerTransition: () => void;
  onCreateProjectRoadmap: (forceRegenerate?: boolean) => void;
  onCreateApplicationMaterials: (forceRegenerate?: boolean) => void;
};

export function ResumeUploadSummary({
  uploadResult,
  activeTargetLabel,
  isBusy,
  isSavedOutputsLoading,
  onRunAnalysis,
  onRunReadinessScores,
  onRunDashboard,
  onRunJobMatches,
  onCreateReport,
  onCreateFullReport,
  onLoadGeneratedOutputs,
  onCreateAIInterpretation,
  onCreateRewriteSuggestions,
  onCreateTailoringPackage,
  onCreateInterviewPrep,
  onCreateClaimVerification,
  onStartMockInterview,
  onCreateOutreachPack,
  onCreateCareerTransition,
  onCreateProjectRoadmap,
  onCreateApplicationMaterials,
}: ResumeUploadSummaryProps) {
  if (!uploadResult) {
    return null;
  }

  return (
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
      <div className="sm:col-span-2">
        <dt className="font-medium">Active target</dt>
        <dd className="text-muted-foreground">
          {activeTargetLabel ?? "No target job selected. Target-aware outputs will use general profile context."}
        </dd>
      </div>
      <ResumeActionsPanel
        isBusy={isBusy}
        isSavedOutputsLoading={isSavedOutputsLoading}
        onCreateAIInterpretation={onCreateAIInterpretation}
        onCreateApplicationMaterials={onCreateApplicationMaterials}
        onCreateCareerTransition={onCreateCareerTransition}
        onCreateClaimVerification={onCreateClaimVerification}
        onCreateFullReport={onCreateFullReport}
        onCreateInterviewPrep={onCreateInterviewPrep}
        onCreateOutreachPack={onCreateOutreachPack}
        onCreateProjectRoadmap={onCreateProjectRoadmap}
        onCreateReport={onCreateReport}
        onCreateRewriteSuggestions={onCreateRewriteSuggestions}
        onCreateTailoringPackage={onCreateTailoringPackage}
        onLoadGeneratedOutputs={onLoadGeneratedOutputs}
        onRunAnalysis={onRunAnalysis}
        onRunDashboard={onRunDashboard}
        onRunJobMatches={onRunJobMatches}
        onRunReadinessScores={onRunReadinessScores}
        onStartMockInterview={onStartMockInterview}
      />
    </dl>
  );
}
