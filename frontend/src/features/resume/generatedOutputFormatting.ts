import { FullCareerReportResult, GeneratedOutput } from "@/lib/api";

export function formatOutputType(outputType: string) {
  const labels: Record<string, string> = {
    ai_interview_prep: "Interview prep",
    ai_claim_verification_questions: "Claim questions",
    ai_outreach_message_pack: "Outreach messages",
    ai_career_transition_analysis: "Career transition",
    ai_readiness_interpretation: "AI interpretation",
    ai_resume_rewrite_suggestions: "Rewrite suggestions",
    ai_resume_tailoring_package: "Tailoring package",
    mvp_basic_report: "Basic report",
    ai_project_roadmap_recommendations: "Project roadmap",
    ai_learning_plan: "Learning plan",
    ai_linkedin_optimization: "LinkedIn optimization",
    ai_application_materials: "Application materials",
    full_career_report: "Full report",
  };
  return labels[outputType] ?? outputType.replace(/_/g, " ");
}

export function generatedOutputSummary(output: GeneratedOutput) {
  const summary = output.result_json.summary;
  if (typeof summary === "string" && summary.trim()) {
    return summary;
  }
  const title = output.result_json.title;
  if (typeof title === "string" && title.trim()) {
    return title;
  }
  return "Saved generated output.";
}

export function exportContentForOutput(output: GeneratedOutput) {
  if (output.result_markdown?.trim()) {
    return output.result_markdown;
  }
  return [
    `# ${formatOutputType(output.output_type)}`,
    "",
    "```json",
    JSON.stringify(output.result_json, null, 2),
    "```",
    "",
  ].join("\n");
}

export function generatedOutputFilename(output: GeneratedOutput) {
  const date = output.created_at ? new Date(output.created_at) : null;
  const datePart =
    date && !Number.isNaN(date.getTime())
      ? date.toISOString().slice(0, 10)
      : "saved-output";
  const typePart = output.output_type.replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "");
  return `snipe-${typePart || "output"}-${datePart}.md`.toLowerCase();
}

export function fullReportFilename(report: FullCareerReportResult) {
  const titlePart = report.title.replace(/[^a-z0-9]+/gi, "-").replace(/^-|-$/g, "");
  return `snipe-${titlePart || "full-career-report"}.md`.toLowerCase();
}

export function downloadJson(filename: string, data: unknown) {
  downloadTextFile(filename, JSON.stringify(data, null, 2), "application/json");
}

export function downloadTextFile(filename: string, content: string, type = "text/plain;charset=utf-8") {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export function formatRoadmapTimeframe(value: string) {
  const labels: Record<string, string> = {
    "7_day": "7-day plan",
    "30_day": "30-day plan",
    "90_day": "90-day plan",
  };
  return labels[value] ?? value.replace(/_/g, " ");
}

export function formatApplyRecommendation(value: string) {
  const labels: Record<string, string> = {
    strong_apply: "Strong apply",
    apply_with_tailoring: "Apply with tailoring",
    build_evidence_first: "Build evidence first",
  };
  return labels[value] ?? value.replace(/_/g, " ");
}

export function formatOutputDate(value: string | null) {
  if (!value) {
    return "Date unavailable";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}
