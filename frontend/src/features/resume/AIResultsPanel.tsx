import { MessageSquare } from "lucide-react";

import { formatRoadmapTimeframe } from "@/features/resume/generatedOutputFormatting";
import { JobField, MessageBlock } from "@/features/resume/resumeDisplay";
import {
  AIInterpretationResult,
  ApplicationMaterialsResult,
  AnswerEvaluationResult,
  CareerTransitionResult,
  ClaimVerificationResult,
  InterviewPrepResult,
  LinkedInOptimizationResult,
  LearningPlanResult,
  LearningPlanStep,
  MockInterviewSession,
  OutreachMessagePack,
  ProjectRoadmapResult,
  ResumeRewriteResult,
  ResumeTailoringPackageResult,
} from "@/lib/api";

type AIResultsPanelProps = {
  aiInterpretationResult: AIInterpretationResult | null;
  rewriteResult: ResumeRewriteResult | null;
  tailoringResult: ResumeTailoringPackageResult | null;
  interviewResult: InterviewPrepResult | null;
  claimVerificationResult: ClaimVerificationResult | null;
  mockInterviewSession: MockInterviewSession | null;
  mockInterviewEvaluation: AnswerEvaluationResult | null;
  mockInterviewAnswer: string;
  outreachResult: OutreachMessagePack | null;
  careerTransitionResult: CareerTransitionResult | null;
  projectRoadmapResult: ProjectRoadmapResult | null;
  learningPlanResult: LearningPlanResult | null;
  linkedInOptimizationResult: LinkedInOptimizationResult | null;
  applicationMaterialsResult: ApplicationMaterialsResult | null;
  isBusy: boolean;
  onMockInterviewAnswerChange: (value: string) => void;
  onSubmitMockAnswer: () => void;
};

export function AIResultsPanel({
  aiInterpretationResult,
  rewriteResult,
  tailoringResult,
  interviewResult,
  claimVerificationResult,
  mockInterviewSession,
  mockInterviewEvaluation,
  mockInterviewAnswer,
  outreachResult,
  careerTransitionResult,
  projectRoadmapResult,
  learningPlanResult,
  linkedInOptimizationResult,
  applicationMaterialsResult,
  isBusy,
  onMockInterviewAnswerChange,
  onSubmitMockAnswer,
}: AIResultsPanelProps) {
  return (
    <>
      {aiInterpretationResult ? (
        <div className="mt-5 border-t border-border pt-5 text-sm">
          <div className="flex items-baseline gap-3">
            <h3 className="text-base font-semibold">AI interpretation</h3>
            <p className="text-xs text-muted-foreground">
              {aiInterpretationResult.cached ? "Cached" : aiInterpretationResult.provider}
            </p>
          </div>
          <p className="mt-2 text-muted-foreground">{aiInterpretationResult.summary}</p>
          <p className="mt-3 text-muted-foreground">{aiInterpretationResult.readiness_explanation}</p>
          <div className="mt-4 grid gap-3">
            {aiInterpretationResult.recommendations.map((item) => (
              <div key={`${item.priority}-${item.title}`} className="border border-border p-3">
                <p className="font-medium">{item.title}</p>
                <p className="mt-1 text-muted-foreground">{item.rationale}</p>
                <p className="mt-2">{item.action}</p>
              </div>
            ))}
          </div>
          {aiInterpretationResult.cautions.length ? (
            <ul className="mt-4 list-disc space-y-1 pl-5 text-muted-foreground">
              {aiInterpretationResult.cautions.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
      {rewriteResult ? (
        <div className="mt-5 border-t border-border pt-5 text-sm">
          <div className="flex items-baseline gap-3">
            <h3 className="text-base font-semibold">Rewrite suggestions</h3>
            <p className="text-xs text-muted-foreground">
              {rewriteResult.cached ? "Cached" : rewriteResult.provider}
            </p>
          </div>
          <p className="mt-2 text-muted-foreground">{rewriteResult.summary}</p>
          <div className="mt-4 grid gap-3">
            {rewriteResult.suggestions.map((item) => (
              <div key={`${item.original}-${item.suggested}`} className="border border-border p-3">
                <p className="font-medium">Original</p>
                <p className="mt-1 text-muted-foreground">{item.original}</p>
                <p className="mt-3 font-medium">Suggested</p>
                <p className="mt-1">{item.suggested}</p>
                <p className="mt-3 text-muted-foreground">{item.rationale}</p>
                <JobField label="Evidence used" values={item.evidence_used} />
                {item.needs_candidate_value ? (
                  <p className="mt-2 text-muted-foreground">Candidate review required before use.</p>
                ) : null}
              </div>
            ))}
          </div>
          {rewriteResult.cautions.length ? (
            <ul className="mt-4 list-disc space-y-1 pl-5 text-muted-foreground">
              {rewriteResult.cautions.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
      {tailoringResult ? (
        <div className="mt-5 border-t border-border pt-5 text-sm">
          <div className="flex items-baseline gap-3">
            <h3 className="text-base font-semibold">Tailoring package</h3>
            <p className="text-xs text-muted-foreground">
              {tailoringResult.cached ? "Cached" : tailoringResult.provider}
            </p>
          </div>
          <p className="mt-2 text-muted-foreground">{tailoringResult.summary}</p>
          <div className="mt-4 border border-border p-3">
            <p className="font-medium">Tailored summary</p>
            <p className="mt-1 text-muted-foreground">{tailoringResult.tailored_summary}</p>
          </div>
          <dl className="mt-4 grid gap-3 sm:grid-cols-2">
            <JobField label="Skill order" values={tailoringResult.skill_order} />
            <JobField label="Missing evidence" values={tailoringResult.missing_evidence_warnings.slice(0, 4)} />
          </dl>
          {tailoringResult.keyword_recommendations.length ? (
            <div className="mt-4 grid gap-3">
              {tailoringResult.keyword_recommendations.slice(0, 6).map((item) => (
                <div key={`${item.keyword}-${item.placement}`} className="border border-border p-3">
                  <p className="font-medium">{item.keyword}</p>
                  <p className="mt-1 text-muted-foreground">{item.placement}</p>
                  <p className="mt-2">{item.reason}</p>
                </div>
              ))}
            </div>
          ) : null}
          {tailoringResult.cautions.length ? (
            <ul className="mt-4 list-disc space-y-1 pl-5 text-muted-foreground">
              {tailoringResult.cautions.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
      {interviewResult ? (
        <div className="mt-5 border-t border-border pt-5 text-sm">
          <div className="flex items-baseline gap-3">
            <h3 className="text-base font-semibold">Interview prep</h3>
            <p className="text-xs text-muted-foreground">
              {interviewResult.cached ? "Cached" : interviewResult.provider}
            </p>
          </div>
          <p className="mt-2 text-muted-foreground">{interviewResult.summary}</p>
          {interviewResult.star_guidance.length ? (
            <ul className="mt-4 list-disc space-y-1 pl-5 text-muted-foreground">
              {interviewResult.star_guidance.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : null}
          {interviewResult.questions.length ? (
            <div className="mt-4 grid gap-3">
              {interviewResult.questions.map((item) => (
                <div key={`${item.category}-${item.question}`} className="border border-border p-3">
                  <p className="text-xs font-medium uppercase text-muted-foreground">
                    {item.category.replace("_", " ")}
                  </p>
                  <p className="mt-2 font-medium">{item.question}</p>
                  <p className="mt-2 text-muted-foreground">{item.why_it_matters}</p>
                  <p className="mt-2">{item.answer_guidance}</p>
                  <JobField label="Evidence to use" values={item.evidence_to_use} />
                  {item.missing_evidence_warning ? (
                    <p className="mt-2 text-muted-foreground">{item.missing_evidence_warning}</p>
                  ) : null}
                </div>
              ))}
            </div>
          ) : null}
          {interviewResult.missing_evidence_warnings.length ? (
            <dl className="mt-4 grid gap-3">
              <JobField label="Missing evidence" values={interviewResult.missing_evidence_warnings.slice(0, 6)} />
            </dl>
          ) : null}
          {interviewResult.cautions.length ? (
            <ul className="mt-4 list-disc space-y-1 pl-5 text-muted-foreground">
              {interviewResult.cautions.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
      {claimVerificationResult ? (
        <div className="mt-5 border-t border-border pt-5 text-sm">
          <div className="flex items-baseline gap-3">
            <h3 className="text-base font-semibold">Claim questions</h3>
            <p className="text-xs text-muted-foreground">
              {claimVerificationResult.cached ? "Cached" : claimVerificationResult.provider}
            </p>
          </div>
          <p className="mt-2 text-muted-foreground">{claimVerificationResult.summary}</p>
          {claimVerificationResult.questions.length ? (
            <div className="mt-4 grid gap-3">
              {claimVerificationResult.questions.map((item) => (
                <div key={`${item.claim}-${item.question}`} className="border border-border p-3">
                  <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between">
                    <p className="font-medium">{item.claim}</p>
                    <p className="text-xs uppercase text-muted-foreground">{item.evidence_strength.replace("_", " ")}</p>
                  </div>
                  <p className="mt-2">{item.question}</p>
                  <p className="mt-2 text-muted-foreground">{item.why_it_matters}</p>
                  <JobField label="Evidence to prepare" values={item.evidence_to_prepare} />
                  {item.caution ? <p className="mt-2 text-muted-foreground">{item.caution}</p> : null}
                </div>
              ))}
            </div>
          ) : null}
          <dl className="mt-4 grid gap-3">
            <JobField label="Evidence strength notes" values={claimVerificationResult.evidence_strength_notes} />
          </dl>
          {claimVerificationResult.cautions.length ? (
            <ul className="mt-4 list-disc space-y-1 pl-5 text-muted-foreground">
              {claimVerificationResult.cautions.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
      {mockInterviewSession ? (
        <div className="mt-5 border-t border-border pt-5 text-sm">
          <div className="flex items-baseline gap-3">
            <h3 className="text-base font-semibold">Mock interview</h3>
            <p className="text-xs text-muted-foreground">
              {mockInterviewSession.status === "completed"
                ? "Completed"
                : `Question ${mockInterviewSession.current_index + 1} of ${mockInterviewSession.questions.length}`}
            </p>
          </div>
          {mockInterviewSession.status === "active" ? (
            <div className="mt-4 border border-border p-3">
              <p className="text-xs font-medium uppercase text-muted-foreground">
                {mockInterviewSession.questions[mockInterviewSession.current_index]?.category.replace("_", " ")}
              </p>
              <p className="mt-2 font-medium">
                {mockInterviewSession.questions[mockInterviewSession.current_index]?.question}
              </p>
              <JobField
                label="Evidence to use"
                values={mockInterviewSession.questions[mockInterviewSession.current_index]?.evidence_to_use ?? []}
              />
              <textarea
                className="mt-3 min-h-28 w-full border border-border px-3 py-2 text-sm"
                placeholder="Type your answer here."
                value={mockInterviewAnswer}
                onChange={(event) => onMockInterviewAnswerChange(event.target.value)}
              />
              <button className="mt-3 inline-flex items-center justify-center gap-2 bg-foreground px-4 py-2 text-sm font-medium text-background" disabled={isBusy || !mockInterviewAnswer.trim()} type="button" onClick={onSubmitMockAnswer}>
                <MessageSquare aria-hidden="true" className="h-4 w-4" />
                Submit answer
              </button>
            </div>
          ) : (
            <p className="mt-2 text-muted-foreground">Completed {mockInterviewSession.transcript.length} interview turns.</p>
          )}
          {mockInterviewEvaluation ? (
            <div className="mt-4 border border-border p-3">
              <div className="flex items-baseline gap-3">
                <p className="font-medium">Latest evaluation</p>
                <p className="text-2xl font-semibold">{mockInterviewEvaluation.overall_score}</p>
              </div>
              <dl className="mt-3 grid gap-3 sm:grid-cols-2">
                <JobField label="Relevance" values={[String(mockInterviewEvaluation.relevance_score)]} />
                <JobField label="Clarity" values={[String(mockInterviewEvaluation.clarity_score)]} />
                <JobField label="Evidence" values={[String(mockInterviewEvaluation.evidence_score)]} />
                <JobField label="Depth" values={[String(mockInterviewEvaluation.depth_score)]} />
                <JobField label="STAR feedback" values={mockInterviewEvaluation.star_feedback} />
                <JobField label="Improvements" values={mockInterviewEvaluation.improvements} />
              </dl>
              <p className="mt-3 font-medium">Follow-up</p>
              <p className="mt-1 text-muted-foreground">{mockInterviewEvaluation.follow_up_question}</p>
              <p className="mt-3 font-medium">Improved answer frame</p>
              <p className="mt-1 text-muted-foreground">{mockInterviewEvaluation.improved_answer}</p>
            </div>
          ) : null}
        </div>
      ) : null}
      {outreachResult ? (
        <div className="mt-5 border-t border-border pt-5 text-sm">
          <div className="flex items-baseline gap-3">
            <h3 className="text-base font-semibold">Outreach messages</h3>
            <p className="text-xs text-muted-foreground">{outreachResult.cached ? "Cached" : outreachResult.provider}</p>
          </div>
          <p className="mt-2 text-muted-foreground">{outreachResult.summary}</p>
          <div className="mt-4 grid gap-3">
            <MessageBlock title="LinkedIn connection" value={outreachResult.linkedin_connection_message} />
            <MessageBlock title="Recruiter outreach" value={outreachResult.recruiter_outreach_message} />
            <MessageBlock title="Job application email" value={outreachResult.job_application_email} />
            <MessageBlock title="Follow-up email" value={outreachResult.follow_up_email} />
            <MessageBlock title="Interview thank-you" value={outreachResult.interview_thank_you_email} />
            <MessageBlock title="Referral request" value={outreachResult.referral_request} />
            <MessageBlock title="Professional intro" value={outreachResult.short_professional_intro} />
          </div>
          <dl className="mt-4 grid gap-3 sm:grid-cols-2">
            <JobField label="Evidence used" values={outreachResult.evidence_used} />
            <JobField label="Missing evidence" values={outreachResult.missing_evidence_warnings} />
          </dl>
        </div>
      ) : null}
      {careerTransitionResult ? (
        <div className="mt-5 border-t border-border pt-5 text-sm">
          <div className="flex items-baseline gap-3">
            <h3 className="text-base font-semibold">Career transition</h3>
            <p className="text-xs text-muted-foreground">{careerTransitionResult.cached ? "Cached" : careerTransitionResult.provider}</p>
          </div>
          <p className="mt-2 text-muted-foreground">{careerTransitionResult.summary}</p>
          <dl className="mt-4 grid gap-3 sm:grid-cols-2">
            <JobField label="Transferable skills" values={careerTransitionResult.transferable_skills} />
            <JobField label="Missing foundations" values={careerTransitionResult.missing_foundational_knowledge} />
            <JobField label="Transitional roles" values={careerTransitionResult.transitional_roles} />
            <JobField label="Recommended projects" values={careerTransitionResult.recommended_projects} />
            <JobField label="Learning sequence" values={careerTransitionResult.learning_sequence} />
            <JobField label="Resume positioning" values={careerTransitionResult.resume_positioning} />
            <JobField label="Interview concerns" values={careerTransitionResult.likely_interview_concerns} />
          </dl>
        </div>
      ) : null}
      {projectRoadmapResult ? (
        <div className="mt-5 border-t border-border pt-5 text-sm">
          <div className="flex items-baseline gap-3">
            <h3 className="text-base font-semibold">Project roadmap</h3>
            <p className="text-xs text-muted-foreground">{projectRoadmapResult.cached ? "Cached" : projectRoadmapResult.provider}</p>
          </div>
          <p className="mt-2 text-muted-foreground">{projectRoadmapResult.summary}</p>
          {projectRoadmapResult.projects.length ? (
            <div className="mt-4 grid gap-3">
              {projectRoadmapResult.projects.map((item) => (
                <div key={item.title} className="border border-border p-3">
                  <p className="font-medium">{item.title}</p>
                  <p className="mt-1 text-muted-foreground">{item.objective}</p>
                  <dl className="mt-3 grid gap-3 sm:grid-cols-2">
                    <JobField label="Skills practiced" values={item.skills_practiced} />
                    <JobField label="Deliverables" values={item.deliverables} />
                    <JobField label="Evidence to add" values={item.evidence_to_add} />
                  </dl>
                  {item.missing_evidence_warning ? <p className="mt-2 text-muted-foreground">{item.missing_evidence_warning}</p> : null}
                </div>
              ))}
            </div>
          ) : null}
          {projectRoadmapResult.roadmap.length ? (
            <div className="mt-4 grid gap-3">
              {projectRoadmapResult.roadmap.map((item) => (
                <div key={item.timeframe} className="border border-border p-3">
                  <p className="font-medium">{formatRoadmapTimeframe(item.timeframe)}</p>
                  <p className="mt-1 text-muted-foreground">{item.focus}</p>
                  <dl className="mt-3 grid gap-3 sm:grid-cols-2">
                    <JobField label="Actions" values={item.actions} />
                    <JobField label="Success criteria" values={item.success_criteria} />
                  </dl>
                </div>
              ))}
            </div>
          ) : null}
          {projectRoadmapResult.missing_evidence_warnings.length ? (
            <dl className="mt-4 grid gap-3">
              <JobField label="Missing evidence" values={projectRoadmapResult.missing_evidence_warnings.slice(0, 6)} />
            </dl>
          ) : null}
          {projectRoadmapResult.cautions.length ? (
            <ul className="mt-4 list-disc space-y-1 pl-5 text-muted-foreground">
              {projectRoadmapResult.cautions.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
      {learningPlanResult ? (
        <div className="mt-5 border-t border-border pt-5 text-sm">
          <div className="flex items-baseline gap-3">
            <h3 className="text-base font-semibold">Learning plan</h3>
            <p className="text-xs text-muted-foreground">{learningPlanResult.cached ? "Cached" : learningPlanResult.provider}</p>
          </div>
          <p className="mt-2 text-muted-foreground">{learningPlanResult.summary}</p>
          <LearningPlanSection title="Daily plan" steps={learningPlanResult.daily_plan} />
          <LearningPlanSection title="Weekly plan" steps={learningPlanResult.weekly_plan} />
          <LearningPlanSection title="Monthly plan" steps={learningPlanResult.monthly_plan} />
          {learningPlanResult.missing_evidence_warnings.length ? (
            <dl className="mt-4 grid gap-3">
              <JobField label="Missing evidence" values={learningPlanResult.missing_evidence_warnings.slice(0, 6)} />
            </dl>
          ) : null}
          {learningPlanResult.cautions.length ? (
            <ul className="mt-4 list-disc space-y-1 pl-5 text-muted-foreground">
              {learningPlanResult.cautions.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
      {linkedInOptimizationResult ? (
        <div className="mt-5 border-t border-border pt-5 text-sm">
          <div className="flex items-baseline gap-3">
            <h3 className="text-base font-semibold">LinkedIn optimization</h3>
            <p className="text-xs text-muted-foreground">{linkedInOptimizationResult.cached ? "Cached" : linkedInOptimizationResult.provider}</p>
          </div>
          <p className="mt-2 text-muted-foreground">{linkedInOptimizationResult.summary}</p>
          <dl className="mt-4 grid gap-3 sm:grid-cols-2">
            <JobField label="Headline options" values={linkedInOptimizationResult.headline_options} />
            <JobField label="Skills to feature" values={linkedInOptimizationResult.skills_to_feature} />
            <JobField label="Profile checklist" values={linkedInOptimizationResult.profile_checklist} />
            <JobField label="Missing evidence" values={linkedInOptimizationResult.missing_evidence_warnings.slice(0, 6)} />
          </dl>
          <div className="mt-4 border border-border p-3">
            <p className="font-medium">About section</p>
            <p className="mt-2 text-muted-foreground">{linkedInOptimizationResult.about_section}</p>
          </div>
          {linkedInOptimizationResult.experience_recommendations.length ? (
            <div className="mt-4 grid gap-3">
              {linkedInOptimizationResult.experience_recommendations.map((item) => (
                <div key={`${item.section}-${item.recommendation}`} className="border border-border p-3">
                  <p className="font-medium">{item.section}</p>
                  <p className="mt-2 text-muted-foreground">{item.recommendation}</p>
                  <JobField label="Evidence to use" values={item.evidence_to_use} />
                  {item.missing_evidence_warning ? (
                    <p className="mt-2 text-muted-foreground">{item.missing_evidence_warning}</p>
                  ) : null}
                </div>
              ))}
            </div>
          ) : null}
          {linkedInOptimizationResult.cautions.length ? (
            <ul className="mt-4 list-disc space-y-1 pl-5 text-muted-foreground">
              {linkedInOptimizationResult.cautions.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
      {applicationMaterialsResult ? (
        <div className="mt-5 border-t border-border pt-5 text-sm">
          <div className="flex items-baseline gap-3">
            <h3 className="text-base font-semibold">Application materials</h3>
            <p className="text-xs text-muted-foreground">{applicationMaterialsResult.cached ? "Cached" : applicationMaterialsResult.provider}</p>
          </div>
          <p className="mt-2 text-muted-foreground">{applicationMaterialsResult.summary}</p>
          <div className="mt-4 grid gap-3">
            <MessageBlock title="Cover letter" value={applicationMaterialsResult.cover_letter} />
            <div className="border border-border p-3">
              <p className="font-medium">Concise cover note</p>
              <p className="mt-2 text-muted-foreground">{applicationMaterialsResult.concise_cover_note}</p>
            </div>
            <MessageBlock title="Email application" value={applicationMaterialsResult.email_application} />
          </div>
          <dl className="mt-4 grid gap-3 sm:grid-cols-2">
            <JobField label="Evidence used" values={applicationMaterialsResult.evidence_used} />
            <JobField label="Missing evidence" values={applicationMaterialsResult.missing_evidence_warnings.slice(0, 6)} />
          </dl>
          {applicationMaterialsResult.cautions.length ? (
            <ul className="mt-4 list-disc space-y-1 pl-5 text-muted-foreground">
              {applicationMaterialsResult.cautions.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </>
  );
}

function LearningPlanSection({ title, steps }: { title: string; steps: LearningPlanStep[] }) {
  if (!steps.length) {
    return null;
  }

  return (
    <div className="mt-4 grid gap-3">
      <h4 className="text-sm font-semibold">{title}</h4>
      {steps.map((item) => (
        <div key={`${item.cadence}-${item.title}`} className="border border-border p-3">
          <p className="font-medium">{item.title}</p>
          <dl className="mt-3 grid gap-3 sm:grid-cols-2">
            <JobField label="Tasks" values={item.tasks} />
            <JobField label="Success criteria" values={item.success_criteria} />
            <JobField label="Practice" values={[item.practice_activity]} />
            <JobField label="Evidence to create" values={[item.evidence_to_create]} />
          </dl>
        </div>
      ))}
    </div>
  );
}
