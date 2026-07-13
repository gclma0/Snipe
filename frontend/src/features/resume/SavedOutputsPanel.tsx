import { Copy, Download, Eye, Trash2 } from "lucide-react";

import {
  exportContentForOutput,
  formatOutputDate,
  formatOutputType,
  generatedOutputSummary,
} from "@/features/resume/generatedOutputFormatting";
import { JobField } from "@/features/resume/resumeDisplay";
import { GeneratedOutput } from "@/lib/api";

const outputTypeFilters = [
  { value: "all", label: "All outputs" },
  { value: "mvp_basic_report", label: "Basic reports" },
  { value: "ai_readiness_interpretation", label: "AI interpretations" },
  { value: "ai_resume_rewrite_suggestions", label: "Rewrite suggestions" },
  { value: "ai_resume_tailoring_package", label: "Tailoring packages" },
  { value: "ai_interview_prep", label: "Interview prep" },
  { value: "ai_claim_verification_questions", label: "Claim questions" },
  { value: "ai_outreach_message_pack", label: "Outreach messages" },
  { value: "ai_career_transition_analysis", label: "Career transition" },
  { value: "ai_project_roadmap_recommendations", label: "Project roadmaps" },
  { value: "ai_application_materials", label: "Application materials" },
  { value: "full_career_report", label: "Full reports" },
] as const;

type SavedOutputsPanelProps = {
  outputs: GeneratedOutput[];
  filteredOutputs: GeneratedOutput[];
  selectedOutput: GeneratedOutput | null;
  filter: string;
  isBusy: boolean;
  isHistoryRefreshing: boolean;
  isSavedOutputsLoading: boolean;
  deletingOutputId: string | null;
  onFilterChange: (value: string) => void;
  onOpen: (output: GeneratedOutput) => void;
  onCopy: (output: GeneratedOutput) => void;
  onDownload: (output: GeneratedOutput) => void;
  onDelete: (output: GeneratedOutput) => void;
};

export function SavedOutputsPanel({
  outputs,
  filteredOutputs,
  selectedOutput,
  filter,
  isBusy,
  isHistoryRefreshing,
  isSavedOutputsLoading,
  deletingOutputId,
  onFilterChange,
  onOpen,
  onCopy,
  onDownload,
  onDelete,
}: SavedOutputsPanelProps) {
  if (!outputs.length) {
    return null;
  }

  return (
    <div className="mt-5 border-t border-border pt-5 text-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-baseline gap-3">
          <h3 className="text-base font-semibold">Saved outputs</h3>
          <p className="text-xs text-muted-foreground">
            {isHistoryRefreshing ? "Refreshing..." : `${filteredOutputs.length} of ${outputs.length}`}
          </p>
        </div>
        <label className="flex items-center gap-2 text-sm font-medium">
          Type
          <select
            className="border border-border bg-white px-3 py-2 text-sm"
            value={filter}
            onChange={(event) => onFilterChange(event.target.value)}
          >
            {outputTypeFilters.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
      </div>
      {filteredOutputs.length ? (
        <div className="mt-4 grid gap-3">
          {filteredOutputs.map((item) => (
            <div key={item.id} className="border border-border p-3">
              <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between">
                <p className="font-medium">{formatOutputType(item.output_type)}</p>
                <p className="text-xs text-muted-foreground">{formatOutputDate(item.created_at)}</p>
              </div>
              <p className="mt-2 text-muted-foreground">{generatedOutputSummary(item)}</p>
              <dl className="mt-3 grid gap-3 sm:grid-cols-2">
                <JobField label="Provider" values={[item.provider ?? "deterministic"]} />
                <JobField label="Version" values={item.prompt_version ? [item.prompt_version] : []} />
              </dl>
              <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:flex-wrap">
                <button className="inline-flex items-center justify-center gap-2 border border-border px-3 py-2 text-sm font-medium" disabled={isSavedOutputsLoading} type="button" onClick={() => onOpen(item)}>
                  <Eye aria-hidden="true" className="h-4 w-4" />
                  View details
                </button>
                <button className="inline-flex items-center justify-center gap-2 border border-border px-3 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => onCopy(item)}>
                  <Copy aria-hidden="true" className="h-4 w-4" />
                  Copy markdown
                </button>
                <button className="inline-flex items-center justify-center gap-2 border border-border px-3 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => onDownload(item)}>
                  <Download aria-hidden="true" className="h-4 w-4" />
                  Download .md
                </button>
                <button className="inline-flex items-center justify-center gap-2 border border-border px-3 py-2 text-sm font-medium" disabled={deletingOutputId === item.id} type="button" onClick={() => onDelete(item)}>
                  <Trash2 aria-hidden="true" className="h-4 w-4" />
                  {deletingOutputId === item.id ? "Deleting..." : "Delete"}
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-4 text-muted-foreground">No saved outputs match this filter.</p>
      )}
      {selectedOutput ? (
        <div className="mt-4 border border-border p-3">
          <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between">
            <p className="font-medium">{formatOutputType(selectedOutput.output_type)} detail</p>
            <p className="text-xs text-muted-foreground">{formatOutputDate(selectedOutput.created_at)}</p>
          </div>
          <dl className="mt-3 grid gap-3 sm:grid-cols-2">
            <JobField label="Provider" values={[selectedOutput.provider ?? "deterministic"]} />
            <JobField label="Model" values={selectedOutput.model_name ? [selectedOutput.model_name] : []} />
            <JobField label="Version" values={selectedOutput.prompt_version ? [selectedOutput.prompt_version] : []} />
            <JobField label="Status" values={[selectedOutput.status]} />
          </dl>
          <pre className="mt-3 max-h-96 overflow-auto whitespace-pre-wrap border border-border bg-muted p-3 text-xs text-muted-foreground">
            {exportContentForOutput(selectedOutput)}
          </pre>
        </div>
      ) : null}
    </div>
  );
}
