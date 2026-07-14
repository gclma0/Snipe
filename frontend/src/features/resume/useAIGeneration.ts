import { useState } from "react";

import {
  downloadTextFile,
  fullReportFilename,
} from "@/features/resume/generatedOutputFormatting";
import {
  AIInterpretationResult,
  ApplicationMaterialsResult,
  AnswerEvaluationResult,
  BasicReportResult,
  CandidateProfile,
  CareerTransitionResult,
  ClaimVerificationResult,
  FullCareerReportResult,
  InterviewPrepResult,
  JobDescriptionResult,
  LearningPlanResult,
  LinkedInOptimizationResult,
  MockInterviewSession,
  OutreachMessagePack,
  ProjectRoadmapResult,
  ResumeRewriteResult,
  ResumeTailoringPackageResult,
  answerMockInterview,
  createAIReadinessInterpretation,
  createApplicationMaterials,
  createBasicReport,
  createCareerTransitionAnalysis,
  createClaimVerificationQuestions,
  createFullReport,
  createInterviewPrep,
  createLearningPlan,
  createLinkedInOptimization,
  createOutreachMessagePack,
  createProjectRoadmap,
  createResumeRewriteSuggestions,
  createResumeTailoringPackage,
  startMockInterview,
} from "@/lib/api";

type UseAIGenerationParams = {
  accessToken: string | null;
  profile: CandidateProfile | null;
  jobResult: JobDescriptionResult | null;
  onBusyChange: (isBusy: boolean) => void;
  onBusyLabelChange: (label: string | null) => void;
  onMessage: (message: string | null) => void;
  refreshGeneratedOutputs: (token: string, profileId: string) => Promise<void>;
};

export function useAIGeneration({
  accessToken,
  profile,
  jobResult,
  onBusyChange,
  onBusyLabelChange,
  onMessage,
  refreshGeneratedOutputs,
}: UseAIGenerationParams) {
  const [reportResult, setReportResult] = useState<BasicReportResult | null>(null);
  const [fullReportResult, setFullReportResult] = useState<FullCareerReportResult | null>(null);
  const [aiInterpretationResult, setAiInterpretationResult] = useState<AIInterpretationResult | null>(null);
  const [rewriteResult, setRewriteResult] = useState<ResumeRewriteResult | null>(null);
  const [tailoringResult, setTailoringResult] = useState<ResumeTailoringPackageResult | null>(null);
  const [interviewResult, setInterviewResult] = useState<InterviewPrepResult | null>(null);
  const [claimVerificationResult, setClaimVerificationResult] = useState<ClaimVerificationResult | null>(null);
  const [mockInterviewSession, setMockInterviewSession] = useState<MockInterviewSession | null>(null);
  const [mockInterviewEvaluation, setMockInterviewEvaluation] = useState<AnswerEvaluationResult | null>(null);
  const [mockInterviewAnswer, setMockInterviewAnswer] = useState("");
  const [outreachResult, setOutreachResult] = useState<OutreachMessagePack | null>(null);
  const [careerTransitionResult, setCareerTransitionResult] = useState<CareerTransitionResult | null>(null);
  const [projectRoadmapResult, setProjectRoadmapResult] = useState<ProjectRoadmapResult | null>(null);
  const [learningPlanResult, setLearningPlanResult] = useState<LearningPlanResult | null>(null);
  const [linkedInOptimizationResult, setLinkedInOptimizationResult] = useState<LinkedInOptimizationResult | null>(null);
  const [applicationMaterialsResult, setApplicationMaterialsResult] = useState<ApplicationMaterialsResult | null>(null);

  function resetAiResults() {
    setAiInterpretationResult(null);
    setRewriteResult(null);
    setTailoringResult(null);
    setInterviewResult(null);
    setClaimVerificationResult(null);
    setMockInterviewSession(null);
    setMockInterviewEvaluation(null);
    setMockInterviewAnswer("");
    setOutreachResult(null);
    setCareerTransitionResult(null);
    setProjectRoadmapResult(null);
    setLearningPlanResult(null);
    setLinkedInOptimizationResult(null);
    setApplicationMaterialsResult(null);
  }

  function resetReportResults() {
    setReportResult(null);
    setFullReportResult(null);
  }

  async function handleCreateReport() {
    if (!accessToken || !profile) {
      return;
    }

    onBusyChange(true);
    onBusyLabelChange("Generating basic report...");
    onMessage(null);
    try {
      const result = await createBasicReport(accessToken, profile.id, jobResult?.id ?? null);
      setReportResult(result);
      await refreshGeneratedOutputs(accessToken, profile.id);
      onMessage("Basic report generated.");
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not generate report.");
    } finally {
      onBusyChange(false);
      onBusyLabelChange(null);
    }
  }

  async function handleCreateFullReport() {
    if (!accessToken || !profile) {
      return;
    }

    onBusyChange(true);
    onBusyLabelChange("Generating full career report...");
    onMessage(null);
    try {
      const result = await createFullReport(accessToken, profile.id, jobResult?.id ?? null);
      setFullReportResult(result);
      await refreshGeneratedOutputs(accessToken, profile.id);
      onMessage("Full career report generated.");
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not generate full report.");
    } finally {
      onBusyChange(false);
      onBusyLabelChange(null);
    }
  }

  function handleDownloadFullReport() {
    if (!fullReportResult) {
      return;
    }

    downloadTextFile(
      fullReportFilename(fullReportResult),
      fullReportResult.markdown,
      "text/markdown;charset=utf-8",
    );
    onMessage("Full report downloaded.");
  }

  async function handleCreateAIInterpretation(forceRegenerate = false) {
    if (!accessToken || !profile) {
      return;
    }

    onBusyChange(true);
    onBusyLabelChange(forceRegenerate ? "Regenerating AI interpretation..." : "Generating AI interpretation...");
    onMessage(null);
    try {
      const result = await createAIReadinessInterpretation(
        accessToken,
        profile.id,
        jobResult?.id ?? null,
        forceRegenerate,
      );
      setAiInterpretationResult(result);
      await refreshGeneratedOutputs(accessToken, profile.id);
      onMessage(result.cached ? "AI interpretation loaded from cache." : "AI interpretation generated.");
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not generate AI interpretation.");
    } finally {
      onBusyChange(false);
      onBusyLabelChange(null);
    }
  }

  async function handleCreateRewriteSuggestions(forceRegenerate = false) {
    if (!accessToken || !profile) {
      return;
    }

    onBusyChange(true);
    onBusyLabelChange(forceRegenerate ? "Regenerating rewrite suggestions..." : "Generating rewrite suggestions...");
    onMessage(null);
    try {
      const result = await createResumeRewriteSuggestions(
        accessToken,
        profile.id,
        jobResult?.id ?? null,
        forceRegenerate,
      );
      setRewriteResult(result);
      await refreshGeneratedOutputs(accessToken, profile.id);
      onMessage(result.cached ? "Rewrite suggestions loaded from cache." : "Rewrite suggestions generated.");
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not generate rewrite suggestions.");
    } finally {
      onBusyChange(false);
      onBusyLabelChange(null);
    }
  }

  async function handleCreateTailoringPackage(forceRegenerate = false) {
    if (!accessToken || !profile) {
      return;
    }

    onBusyChange(true);
    onBusyLabelChange(forceRegenerate ? "Regenerating tailoring package..." : "Generating tailoring package...");
    onMessage(null);
    try {
      const result = await createResumeTailoringPackage(
        accessToken,
        profile.id,
        jobResult?.id ?? null,
        forceRegenerate,
      );
      setTailoringResult(result);
      await refreshGeneratedOutputs(accessToken, profile.id);
      onMessage(result.cached ? "Tailoring package loaded from cache." : "Tailoring package generated.");
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not generate tailoring package.");
    } finally {
      onBusyChange(false);
      onBusyLabelChange(null);
    }
  }

  async function handleCreateInterviewPrep(forceRegenerate = false) {
    if (!accessToken || !profile) {
      return;
    }

    onBusyChange(true);
    onBusyLabelChange(forceRegenerate ? "Regenerating interview prep..." : "Generating interview prep...");
    onMessage(null);
    try {
      const result = await createInterviewPrep(
        accessToken,
        profile.id,
        jobResult?.id ?? null,
        forceRegenerate,
      );
      setInterviewResult(result);
      await refreshGeneratedOutputs(accessToken, profile.id);
      onMessage(result.cached ? "Interview prep loaded from cache." : "Interview prep generated.");
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not generate interview prep.");
    } finally {
      onBusyChange(false);
      onBusyLabelChange(null);
    }
  }

  async function handleCreateClaimVerification(forceRegenerate = false) {
    if (!accessToken || !profile) {
      return;
    }

    onBusyChange(true);
    onBusyLabelChange(forceRegenerate ? "Regenerating claim questions..." : "Generating claim questions...");
    onMessage(null);
    try {
      const result = await createClaimVerificationQuestions(
        accessToken,
        profile.id,
        jobResult?.id ?? null,
        forceRegenerate,
      );
      setClaimVerificationResult(result);
      await refreshGeneratedOutputs(accessToken, profile.id);
      onMessage(result.cached ? "Claim questions loaded from cache." : "Claim questions generated.");
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not generate claim questions.");
    } finally {
      onBusyChange(false);
      onBusyLabelChange(null);
    }
  }

  async function handleStartMockInterview() {
    if (!accessToken || !profile) {
      return;
    }

    onBusyChange(true);
    onBusyLabelChange("Starting mock interview...");
    onMessage(null);
    try {
      const result = await startMockInterview(accessToken, profile.id, jobResult?.id ?? null, 5);
      setMockInterviewSession(result);
      setMockInterviewEvaluation(null);
      setMockInterviewAnswer("");
      onMessage("Mock interview started.");
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not start mock interview.");
    } finally {
      onBusyChange(false);
      onBusyLabelChange(null);
    }
  }

  async function handleSubmitMockAnswer() {
    if (!accessToken || !profile || !mockInterviewSession || !mockInterviewAnswer.trim()) {
      return;
    }

    onBusyChange(true);
    onBusyLabelChange("Evaluating interview answer...");
    onMessage(null);
    try {
      const result = await answerMockInterview(
        accessToken,
        profile.id,
        mockInterviewSession,
        mockInterviewAnswer,
      );
      setMockInterviewSession(result.session);
      setMockInterviewEvaluation(result.evaluation);
      setMockInterviewAnswer("");
      onMessage(result.session.status === "completed" ? "Mock interview completed." : "Answer evaluated.");
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not evaluate answer.");
    } finally {
      onBusyChange(false);
      onBusyLabelChange(null);
    }
  }

  async function handleCreateOutreachPack() {
    if (!accessToken || !profile) {
      return;
    }

    onBusyChange(true);
    onBusyLabelChange("Generating outreach messages...");
    onMessage(null);
    try {
      const result = await createOutreachMessagePack(accessToken, profile.id, jobResult?.id ?? null);
      setOutreachResult(result);
      await refreshGeneratedOutputs(accessToken, profile.id);
      onMessage(result.cached ? "Outreach messages loaded from cache." : "Outreach messages generated.");
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not generate outreach messages.");
    } finally {
      onBusyChange(false);
      onBusyLabelChange(null);
    }
  }

  async function handleCreateCareerTransition() {
    if (!accessToken || !profile) {
      return;
    }

    onBusyChange(true);
    onBusyLabelChange("Generating career transition analysis...");
    onMessage(null);
    try {
      const result = await createCareerTransitionAnalysis(accessToken, profile.id, jobResult?.id ?? null);
      setCareerTransitionResult(result);
      await refreshGeneratedOutputs(accessToken, profile.id);
      onMessage(result.cached ? "Career transition loaded from cache." : "Career transition generated.");
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not generate career transition analysis.");
    } finally {
      onBusyChange(false);
      onBusyLabelChange(null);
    }
  }

  async function handleCreateProjectRoadmap(forceRegenerate = false) {
    if (!accessToken || !profile) {
      return;
    }

    onBusyChange(true);
    onBusyLabelChange(forceRegenerate ? "Regenerating project roadmap..." : "Generating project roadmap...");
    onMessage(null);
    try {
      const result = await createProjectRoadmap(
        accessToken,
        profile.id,
        jobResult?.id ?? null,
        forceRegenerate,
      );
      setProjectRoadmapResult(result);
      await refreshGeneratedOutputs(accessToken, profile.id);
      onMessage(result.cached ? "Project roadmap loaded from cache." : "Project roadmap generated.");
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not generate project roadmap.");
    } finally {
      onBusyChange(false);
      onBusyLabelChange(null);
    }
  }

  async function handleCreateApplicationMaterials(forceRegenerate = false) {
    if (!accessToken || !profile) {
      return;
    }

    onBusyChange(true);
    onBusyLabelChange(forceRegenerate ? "Regenerating application materials..." : "Generating application materials...");
    onMessage(null);
    try {
      const result = await createApplicationMaterials(
        accessToken,
        profile.id,
        jobResult?.id ?? null,
        forceRegenerate,
      );
      setApplicationMaterialsResult(result);
      await refreshGeneratedOutputs(accessToken, profile.id);
      onMessage(
        result.cached ? "Application materials loaded from cache." : "Application materials generated.",
      );
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not generate application materials.");
    } finally {
      onBusyChange(false);
      onBusyLabelChange(null);
    }
  }

  async function handleCreateLearningPlan(forceRegenerate = false) {
    if (!accessToken || !profile) {
      return;
    }

    onBusyChange(true);
    onBusyLabelChange(forceRegenerate ? "Regenerating learning plan..." : "Generating learning plan...");
    onMessage(null);
    try {
      const result = await createLearningPlan(
        accessToken,
        profile.id,
        jobResult?.id ?? null,
        forceRegenerate,
      );
      setLearningPlanResult(result);
      await refreshGeneratedOutputs(accessToken, profile.id);
      onMessage(result.cached ? "Learning plan loaded from cache." : "Learning plan generated.");
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not generate learning plan.");
    } finally {
      onBusyChange(false);
      onBusyLabelChange(null);
    }
  }

  async function handleCreateLinkedInOptimization(forceRegenerate = false) {
    if (!accessToken || !profile) {
      return;
    }

    onBusyChange(true);
    onBusyLabelChange(forceRegenerate ? "Regenerating LinkedIn optimization..." : "Generating LinkedIn optimization...");
    onMessage(null);
    try {
      const result = await createLinkedInOptimization(
        accessToken,
        profile.id,
        jobResult?.id ?? null,
        forceRegenerate,
      );
      setLinkedInOptimizationResult(result);
      await refreshGeneratedOutputs(accessToken, profile.id);
      onMessage(
        result.cached ? "LinkedIn optimization loaded from cache." : "LinkedIn optimization generated.",
      );
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not generate LinkedIn optimization.");
    } finally {
      onBusyChange(false);
      onBusyLabelChange(null);
    }
  }

  return {
    aiInterpretationResult,
    applicationMaterialsResult,
    careerTransitionResult,
    claimVerificationResult,
    fullReportResult,
    handleCreateAIInterpretation,
    handleCreateApplicationMaterials,
    handleCreateCareerTransition,
    handleCreateClaimVerification,
    handleCreateFullReport,
    handleCreateInterviewPrep,
    handleCreateLearningPlan,
    handleCreateLinkedInOptimization,
    handleCreateOutreachPack,
    handleCreateProjectRoadmap,
    handleCreateReport,
    handleCreateRewriteSuggestions,
    handleCreateTailoringPackage,
    handleDownloadFullReport,
    handleStartMockInterview,
    handleSubmitMockAnswer,
    interviewResult,
    learningPlanResult,
    linkedInOptimizationResult,
    mockInterviewAnswer,
    mockInterviewEvaluation,
    mockInterviewSession,
    outreachResult,
    projectRoadmapResult,
    reportResult,
    resetAiResults,
    resetReportResults,
    rewriteResult,
    setApplicationMaterialsResult,
    setInterviewResult,
    setMockInterviewAnswer,
    setTailoringResult,
    tailoringResult,
  };
}
