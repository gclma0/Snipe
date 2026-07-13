import {
  BriefcaseBusiness,
  ClipboardCheck,
  Gauge,
  GitCompareArrows,
  History,
  LayoutDashboard,
  MessageSquare,
  ScrollText,
  Sparkles,
} from "lucide-react";

type ResumeActionsPanelProps = {
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
  onCreateLearningPlan: (forceRegenerate?: boolean) => void;
  onCreateLinkedInOptimization: (forceRegenerate?: boolean) => void;
  onCreateApplicationMaterials: (forceRegenerate?: boolean) => void;
};

export function ResumeActionsPanel({
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
  onCreateLearningPlan,
  onCreateLinkedInOptimization,
  onCreateApplicationMaterials,
}: ResumeActionsPanelProps) {
  return (
    <div className="grid gap-4 pt-2 sm:col-span-2">
      <div>
        <h3 className="text-sm font-semibold">Analysis</h3>
        <div className="mt-2 grid gap-2 sm:grid-cols-2">
          <button className="inline-flex items-center justify-center gap-2 bg-foreground px-4 py-2 text-sm font-medium text-background" disabled={isBusy} type="button" onClick={onRunAnalysis}>
            <Gauge aria-hidden="true" className="h-4 w-4" />
            Resume quality
          </button>
          <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={onRunReadinessScores}>
            <ClipboardCheck aria-hidden="true" className="h-4 w-4" />
            Readiness scores
          </button>
          <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={onRunDashboard}>
            <LayoutDashboard aria-hidden="true" className="h-4 w-4" />
            Readiness dashboard
          </button>
          <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={onRunJobMatches}>
            <BriefcaseBusiness aria-hidden="true" className="h-4 w-4" />
            Job matches
          </button>
          <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={onCreateReport}>
            <ScrollText aria-hidden="true" className="h-4 w-4" />
            Basic report
          </button>
          <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={onCreateFullReport}>
            <ScrollText aria-hidden="true" className="h-4 w-4" />
            Full report
          </button>
        </div>
      </div>
      <div>
        <h3 className="text-sm font-semibold">Saved outputs</h3>
        <div className="mt-2 grid gap-2 sm:grid-cols-2">
          <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isSavedOutputsLoading} type="button" onClick={onLoadGeneratedOutputs}>
            <History aria-hidden="true" className="h-4 w-4" />
            {isSavedOutputsLoading ? "Loading..." : "Load history"}
          </button>
        </div>
      </div>
      <div>
        <h3 className="text-sm font-semibold">AI generation</h3>
        <div className="mt-2 grid gap-2 sm:grid-cols-2">
          <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => onCreateAIInterpretation(false)}>
            <Sparkles aria-hidden="true" className="h-4 w-4" />
            AI interpretation
          </button>
          <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => onCreateAIInterpretation(true)}>
            <Sparkles aria-hidden="true" className="h-4 w-4" />
            Regenerate interpretation
          </button>
          <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => onCreateRewriteSuggestions(false)}>
            <ScrollText aria-hidden="true" className="h-4 w-4" />
            Rewrite suggestions
          </button>
          <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => onCreateRewriteSuggestions(true)}>
            <ScrollText aria-hidden="true" className="h-4 w-4" />
            Regenerate rewrites
          </button>
          <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => onCreateTailoringPackage(false)}>
            <ClipboardCheck aria-hidden="true" className="h-4 w-4" />
            Tailoring package
          </button>
          <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => onCreateTailoringPackage(true)}>
            <ClipboardCheck aria-hidden="true" className="h-4 w-4" />
            Regenerate tailoring
          </button>
          <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => onCreateInterviewPrep(false)}>
            <MessageSquare aria-hidden="true" className="h-4 w-4" />
            Interview prep
          </button>
          <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => onCreateInterviewPrep(true)}>
            <MessageSquare aria-hidden="true" className="h-4 w-4" />
            Regenerate prep
          </button>
          <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => onCreateClaimVerification(false)}>
            <MessageSquare aria-hidden="true" className="h-4 w-4" />
            Claim questions
          </button>
          <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => onCreateClaimVerification(true)}>
            <MessageSquare aria-hidden="true" className="h-4 w-4" />
            Regenerate claims
          </button>
          <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={onStartMockInterview}>
            <MessageSquare aria-hidden="true" className="h-4 w-4" />
            Mock interview
          </button>
          <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={onCreateOutreachPack}>
            <MessageSquare aria-hidden="true" className="h-4 w-4" />
            Outreach messages
          </button>
          <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={onCreateCareerTransition}>
            <GitCompareArrows aria-hidden="true" className="h-4 w-4" />
            Career transition
          </button>
          <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => onCreateProjectRoadmap(false)}>
            <LayoutDashboard aria-hidden="true" className="h-4 w-4" />
            Project roadmap
          </button>
          <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => onCreateProjectRoadmap(true)}>
            <LayoutDashboard aria-hidden="true" className="h-4 w-4" />
            Regenerate roadmap
          </button>
          <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => onCreateLearningPlan(false)}>
            <LayoutDashboard aria-hidden="true" className="h-4 w-4" />
            Learning plan
          </button>
          <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => onCreateLearningPlan(true)}>
            <LayoutDashboard aria-hidden="true" className="h-4 w-4" />
            Regenerate plan
          </button>
          <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => onCreateLinkedInOptimization(false)}>
            <MessageSquare aria-hidden="true" className="h-4 w-4" />
            LinkedIn optimization
          </button>
          <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => onCreateLinkedInOptimization(true)}>
            <MessageSquare aria-hidden="true" className="h-4 w-4" />
            Regenerate LinkedIn
          </button>
          <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => onCreateApplicationMaterials(false)}>
            <ScrollText aria-hidden="true" className="h-4 w-4" />
            Application materials
          </button>
          <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => onCreateApplicationMaterials(true)}>
            <ScrollText aria-hidden="true" className="h-4 w-4" />
            Regenerate materials
          </button>
        </div>
      </div>
    </div>
  );
}
