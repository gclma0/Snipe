import { zodResolver } from "@hookform/resolvers/zod";
import {
  BriefcaseBusiness,
  ClipboardCheck,
  Download,
  Gauge,
  GitCompareArrows,
  History,
  LayoutDashboard,
  MessageSquare,
  ScrollText,
  Sparkles,
} from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { SavedOutputsPanel } from "@/features/resume/SavedOutputsPanel";
import { ProfileSourcesPanel } from "@/features/resume/ProfileSourcesPanel";
import { exportContentForOutput, formatApplyRecommendation, formatRoadmapTimeframe, fullReportFilename, generatedOutputFilename } from "@/features/resume/generatedOutputFormatting";
import { JobField, MessageBlock, ScoreCard } from "@/features/resume/resumeDisplay";
import {
  BasicReportResult,
  AIInterpretationResult,
  ApplicationMaterialsResult,
  AnswerEvaluationResult,
  CareerTransitionResult,
  CandidateProfile,
  ClaimVerificationResult,
  DeterministicScoreResult,
  FullCareerReportResult,
  GeneratedOutput,
  GitHubSourceResult,
  InterviewPrepResult,
  JobDescriptionResult,
  JobMatchResult,
  LinkedInSourceResult,
  MockInterviewSession,
  OutreachMessagePack,
  PortfolioSourceResult,
  PrivacyDataSummaryResult,
  ProjectRoadmapResult,
  ReadinessDashboardResult,
  ResumeQualityResult,
  ResumeRewriteResult,
  ResumeTailoringPackageResult,
  ResumeUploadResult,
  SkillGapResult,
  addGitHubSource,
  addLinkedInTextSource,
  addPortfolioSource,
  answerMockInterview,
  createAIReadinessInterpretation,
  createApplicationMaterials,
  createBasicReport,
  createCareerTransitionAnalysis,
  createClaimVerificationQuestions,
  createFullReport,
  createInterviewPrep,
  createOutreachMessagePack,
  createJobDescription,
  createProjectRoadmap,
  createResumeRewriteSuggestions,
  createResumeTailoringPackage,
  createProfile,
  deleteGeneratedOutput,
  deleteProfileData,
  deleteProfileDocuments,
  getPrivacyDataSummary,
  getGeneratedOutput,
  listGeneratedOutputs,
  listProfiles,
  runAtsReadinessAnalysis,
  runJobMatches,
  runProfileCompletenessAnalysis,
  runReadinessDashboard,
  runResumeQualityAnalysis,
  runSkillGapAnalysis,
  startMockInterview,
  uploadLinkedInSource,
  uploadResume,
} from "@/lib/api";

const profileSchema = z.object({
  career_goal: z.string().min(1, "Career goal is required.").max(120),
  preferred_role: z.string().min(1, "Preferred role is required.").max(120),
});

const jobDescriptionSchema = z.object({
  text: z.string().min(100, "Paste at least 100 characters from the job description.").max(60000),
});

const githubSchema = z.object({
  username_or_url: z.string().min(1, "GitHub username or URL is required.").max(120),
});

const portfolioSchema = z.object({
  url: z.string().min(1, "Portfolio URL is required.").max(500),
});

const linkedInSchema = z.object({
  text: z.string().min(50, "Paste at least 50 characters from LinkedIn.").max(60000),
});

type ProfileValues = z.infer<typeof profileSchema>;
type JobDescriptionValues = z.infer<typeof jobDescriptionSchema>;
type GitHubValues = z.infer<typeof githubSchema>;
type PortfolioValues = z.infer<typeof portfolioSchema>;
type LinkedInValues = z.infer<typeof linkedInSchema>;

type ResumeWorkflowProps = {
  accessToken: string | null;
};

export function ResumeWorkflow({ accessToken }: ResumeWorkflowProps) {
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [uploadResult, setUploadResult] = useState<ResumeUploadResult | null>(null);
  const [qualityResult, setQualityResult] = useState<ResumeQualityResult | null>(null);
  const [atsResult, setAtsResult] = useState<DeterministicScoreResult | null>(null);
  const [completenessResult, setCompletenessResult] = useState<DeterministicScoreResult | null>(null);
  const [jobResult, setJobResult] = useState<JobDescriptionResult | null>(null);
  const [githubResult, setGithubResult] = useState<GitHubSourceResult | null>(null);
  const [portfolioResult, setPortfolioResult] = useState<PortfolioSourceResult | null>(null);
  const [linkedInResult, setLinkedInResult] = useState<LinkedInSourceResult | null>(null);
  const [skillGapResult, setSkillGapResult] = useState<SkillGapResult | null>(null);
  const [jobMatchResult, setJobMatchResult] = useState<JobMatchResult | null>(null);
  const [dashboardResult, setDashboardResult] = useState<ReadinessDashboardResult | null>(null);
  const [reportResult, setReportResult] = useState<BasicReportResult | null>(null);
  const [fullReportResult, setFullReportResult] = useState<FullCareerReportResult | null>(null);
  const [privacySummary, setPrivacySummary] = useState<PrivacyDataSummaryResult | null>(null);
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
  const [applicationMaterialsResult, setApplicationMaterialsResult] = useState<ApplicationMaterialsResult | null>(null);
  const [generatedOutputs, setGeneratedOutputs] = useState<GeneratedOutput[]>([]);
  const [generatedOutputFilter, setGeneratedOutputFilter] = useState("all");
  const [selectedGeneratedOutput, setSelectedGeneratedOutput] = useState<GeneratedOutput | null>(null);
  const [deletingGeneratedOutputId, setDeletingGeneratedOutputId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isBusy, setIsBusy] = useState(false);
  const [busyLabel, setBusyLabel] = useState<string | null>(null);
  const [isSavedOutputsLoading, setIsSavedOutputsLoading] = useState(false);
  const [isHistoryRefreshing, setIsHistoryRefreshing] = useState(false);
  const filteredGeneratedOutputs =
    generatedOutputFilter === "all"
      ? generatedOutputs
      : generatedOutputs.filter((item) => item.output_type === generatedOutputFilter);
  const form = useForm<ProfileValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      career_goal: "Prepare for a target role",
      preferred_role: "",
    },
  });
  const jobForm = useForm<JobDescriptionValues>({
    resolver: zodResolver(jobDescriptionSchema),
    defaultValues: {
      text: "",
    },
  });
  const githubForm = useForm<GitHubValues>({
    resolver: zodResolver(githubSchema),
    defaultValues: {
      username_or_url: "",
    },
  });
  const portfolioForm = useForm<PortfolioValues>({
    resolver: zodResolver(portfolioSchema),
    defaultValues: {
      url: "",
    },
  });
  const linkedInForm = useForm<LinkedInValues>({
    resolver: zodResolver(linkedInSchema),
    defaultValues: {
      text: "",
    },
  });

  async function handleCreateProfile(values: ProfileValues) {
    if (!accessToken) {
      setMessage("Sign in before creating a profile.");
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const created = await createProfile(accessToken, values);
      setProfile(created);
      setUploadResult(null);
      setQualityResult(null);
      setAtsResult(null);
      setCompletenessResult(null);
      setJobResult(null);
      setGithubResult(null);
      setPortfolioResult(null);
      setLinkedInResult(null);
      setSkillGapResult(null);
      setJobMatchResult(null);
      setDashboardResult(null);
      setReportResult(null);
      setFullReportResult(null);
      setPrivacySummary(null);
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
      setApplicationMaterialsResult(null);
      setGeneratedOutputs([]);
      setGeneratedOutputFilter("all");
      setSelectedGeneratedOutput(null);
      setMessage("Profile created.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not create profile.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleLoadLatestProfile() {
    if (!accessToken) {
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const profiles = await listProfiles(accessToken);
      const latestProfile = profiles[0] ?? null;
      if (!latestProfile) {
        setMessage("No saved profiles found yet.");
        return;
      }

      const outputs = await listGeneratedOutputs(accessToken, latestProfile.id);
      setProfile(latestProfile);
      setUploadResult(null);
      setQualityResult(null);
      setAtsResult(null);
      setCompletenessResult(null);
      setJobResult(null);
      setGithubResult(null);
      setPortfolioResult(null);
      setLinkedInResult(null);
      setSkillGapResult(null);
      setJobMatchResult(null);
      setDashboardResult(null);
      setReportResult(null);
      setFullReportResult(null);
      setPrivacySummary(null);
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
      setApplicationMaterialsResult(null);
      setGeneratedOutputs(outputs);
      setGeneratedOutputFilter("all");
      setSelectedGeneratedOutput(null);
      setMessage(outputs.length ? "Latest profile and saved outputs loaded." : "Latest profile loaded. No saved outputs found yet.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not load latest profile.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleCreateJobDescription(values: JobDescriptionValues) {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const result = await createJobDescription(accessToken, profile.id, values.text);
      setJobResult(result);
      setSkillGapResult(null);
      setJobMatchResult(null);
      setDashboardResult(null);
      setReportResult(null);
      setFullReportResult(null);
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
      setApplicationMaterialsResult(null);
      setGeneratedOutputs([]);
      setGeneratedOutputFilter("all");
      setSelectedGeneratedOutput(null);
      setMessage("Job description analyzed.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not analyze job description.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleAddGitHub(values: GitHubValues) {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const result = await addGitHubSource(accessToken, profile.id, values.username_or_url);
      setGithubResult(result);
      setMessage("GitHub source analyzed.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not analyze GitHub source.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleAddPortfolio(values: PortfolioValues) {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const result = await addPortfolioSource(accessToken, profile.id, values.url);
      setPortfolioResult(result);
      setMessage("Portfolio source analyzed.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not analyze portfolio source.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleAddLinkedInText(values: LinkedInValues) {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const result = await addLinkedInTextSource(accessToken, profile.id, values.text);
      setLinkedInResult(result);
      setMessage("LinkedIn source analyzed.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not analyze LinkedIn source.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleUploadLinkedIn(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file || !accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const result = await uploadLinkedInSource(accessToken, profile.id, file);
      setLinkedInResult(result);
      setMessage("LinkedIn upload analyzed.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not upload LinkedIn file.");
    } finally {
      setIsBusy(false);
      event.target.value = "";
    }
  }

  async function handleUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file || !accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const result = await uploadResume(accessToken, profile.id, file);
      setUploadResult(result);
      setQualityResult(null);
      setAtsResult(null);
      setCompletenessResult(null);
      setGithubResult(null);
      setPortfolioResult(null);
      setLinkedInResult(null);
      setSkillGapResult(null);
      setJobMatchResult(null);
      setDashboardResult(null);
      setReportResult(null);
      setFullReportResult(null);
      setPrivacySummary(null);
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
      setApplicationMaterialsResult(null);
      setGeneratedOutputs([]);
      setGeneratedOutputFilter("all");
      setSelectedGeneratedOutput(null);
      setMessage("Resume uploaded and parsed.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not upload resume.");
    } finally {
      setIsBusy(false);
      event.target.value = "";
    }
  }

  async function handleDeleteProfile() {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      await deleteProfileData(accessToken, profile.id);
      setProfile(null);
      setUploadResult(null);
      setQualityResult(null);
      setAtsResult(null);
      setCompletenessResult(null);
      setJobResult(null);
      setGithubResult(null);
      setPortfolioResult(null);
      setLinkedInResult(null);
      setSkillGapResult(null);
      setJobMatchResult(null);
      setDashboardResult(null);
      setReportResult(null);
      setFullReportResult(null);
      setPrivacySummary(null);
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
      setApplicationMaterialsResult(null);
      setGeneratedOutputs([]);
      setGeneratedOutputFilter("all");
      setSelectedGeneratedOutput(null);
      setMessage("Profile data deleted.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not delete profile data.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleLoadPrivacySummary() {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const result = await getPrivacyDataSummary(accessToken, profile.id);
      setPrivacySummary(result);
      setMessage("Privacy summary loaded.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not load privacy summary.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleDeleteDocumentsOnly() {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const result = await deleteProfileDocuments(accessToken, profile.id);
      setMessage(`Deleted ${result.deleted_storage_objects} stored document object(s).`);
      await handleLoadPrivacySummary();
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not delete stored documents.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleCreateReport() {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setBusyLabel("Generating basic report...");
    setMessage(null);
    try {
      const result = await createBasicReport(accessToken, profile.id, jobResult?.id ?? null);
      setReportResult(result);
      await refreshGeneratedOutputs(accessToken, profile.id);
      setMessage("Basic report generated.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not generate report.");
    } finally {
      setIsBusy(false);
      setBusyLabel(null);
    }
  }

  async function handleCreateFullReport() {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setBusyLabel("Generating full career report...");
    setMessage(null);
    try {
      const result = await createFullReport(accessToken, profile.id, jobResult?.id ?? null);
      setFullReportResult(result);
      await refreshGeneratedOutputs(accessToken, profile.id);
      setMessage("Full career report generated.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not generate full report.");
    } finally {
      setIsBusy(false);
      setBusyLabel(null);
    }
  }

  async function handleLoadGeneratedOutputs() {
    if (!accessToken || !profile) {
      return;
    }

    setIsSavedOutputsLoading(true);
    setMessage(null);
    try {
      const result = await listGeneratedOutputs(accessToken, profile.id);
      setGeneratedOutputs(result);
      setSelectedGeneratedOutput(null);
      setMessage(result.length ? "Saved outputs loaded." : "No saved outputs found yet.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not load saved outputs.");
    } finally {
      setIsSavedOutputsLoading(false);
    }
  }

  async function refreshGeneratedOutputs(token: string, profileId: string) {
    setIsHistoryRefreshing(true);
    try {
      const result = await listGeneratedOutputs(token, profileId);
      setGeneratedOutputs(result);
      setSelectedGeneratedOutput((current) => {
        if (!current) {
          return null;
        }
        return result.find((item) => item.id === current.id) ?? null;
      });
    } catch {
      // Refreshing history should not hide a successful generation result.
    } finally {
      setIsHistoryRefreshing(false);
    }
  }

  async function handleCopyGeneratedOutput(output: GeneratedOutput) {
    const content = exportContentForOutput(output);
    try {
      await navigator.clipboard.writeText(content);
      setMessage("Saved output copied.");
    } catch {
      setMessage("Could not copy saved output.");
    }
  }

  async function handleOpenGeneratedOutput(output: GeneratedOutput) {
    if (!accessToken || !profile) {
      return;
    }

    setIsSavedOutputsLoading(true);
    setMessage(null);
    try {
      const result = await getGeneratedOutput(accessToken, profile.id, output.id);
      setSelectedGeneratedOutput(result);
      setGeneratedOutputs((current) =>
        current.map((item) => (item.id === result.id ? result : item)),
      );
      setMessage("Saved output opened.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not open saved output.");
    } finally {
      setIsSavedOutputsLoading(false);
    }
  }

  async function handleDeleteGeneratedOutput(output: GeneratedOutput) {
    if (!accessToken || !profile) {
      return;
    }

    setDeletingGeneratedOutputId(output.id);
    setMessage(null);
    try {
      await deleteGeneratedOutput(accessToken, profile.id, output.id);
      setGeneratedOutputs((current) => current.filter((item) => item.id !== output.id));
      setSelectedGeneratedOutput((current) => (current?.id === output.id ? null : current));
      setMessage("Saved output deleted.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not delete saved output.");
    } finally {
      setDeletingGeneratedOutputId(null);
    }
  }

  function handleDownloadGeneratedOutput(output: GeneratedOutput) {
    const content = exportContentForOutput(output);
    const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = generatedOutputFilename(output);
    document.body.append(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    setMessage("Saved output downloaded.");
  }

  function handleDownloadFullReport() {
    if (!fullReportResult) {
      return;
    }

    const blob = new Blob([fullReportResult.markdown], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = fullReportFilename(fullReportResult);
    document.body.append(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    setMessage("Full report downloaded.");
  }

  async function handleCreateAIInterpretation(forceRegenerate = false) {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setBusyLabel(forceRegenerate ? "Regenerating AI interpretation..." : "Generating AI interpretation...");
    setMessage(null);
    try {
      const result = await createAIReadinessInterpretation(
        accessToken,
        profile.id,
        jobResult?.id ?? null,
        forceRegenerate,
      );
      setAiInterpretationResult(result);
      await refreshGeneratedOutputs(accessToken, profile.id);
      setMessage(result.cached ? "AI interpretation loaded from cache." : "AI interpretation generated.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not generate AI interpretation.");
    } finally {
      setIsBusy(false);
      setBusyLabel(null);
    }
  }

  async function handleCreateRewriteSuggestions(forceRegenerate = false) {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setBusyLabel(forceRegenerate ? "Regenerating rewrite suggestions..." : "Generating rewrite suggestions...");
    setMessage(null);
    try {
      const result = await createResumeRewriteSuggestions(
        accessToken,
        profile.id,
        jobResult?.id ?? null,
        forceRegenerate,
      );
      setRewriteResult(result);
      await refreshGeneratedOutputs(accessToken, profile.id);
      setMessage(result.cached ? "Rewrite suggestions loaded from cache." : "Rewrite suggestions generated.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not generate rewrite suggestions.");
    } finally {
      setIsBusy(false);
      setBusyLabel(null);
    }
  }

  async function handleCreateTailoringPackage(forceRegenerate = false) {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setBusyLabel(forceRegenerate ? "Regenerating tailoring package..." : "Generating tailoring package...");
    setMessage(null);
    try {
      const result = await createResumeTailoringPackage(
        accessToken,
        profile.id,
        jobResult?.id ?? null,
        forceRegenerate,
      );
      setTailoringResult(result);
      await refreshGeneratedOutputs(accessToken, profile.id);
      setMessage(result.cached ? "Tailoring package loaded from cache." : "Tailoring package generated.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not generate tailoring package.");
    } finally {
      setIsBusy(false);
      setBusyLabel(null);
    }
  }

  async function handleCreateInterviewPrep(forceRegenerate = false) {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setBusyLabel(forceRegenerate ? "Regenerating interview prep..." : "Generating interview prep...");
    setMessage(null);
    try {
      const result = await createInterviewPrep(
        accessToken,
        profile.id,
        jobResult?.id ?? null,
        forceRegenerate,
      );
      setInterviewResult(result);
      await refreshGeneratedOutputs(accessToken, profile.id);
      setMessage(result.cached ? "Interview prep loaded from cache." : "Interview prep generated.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not generate interview prep.");
    } finally {
      setIsBusy(false);
      setBusyLabel(null);
    }
  }

  async function handleCreateClaimVerification(forceRegenerate = false) {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setBusyLabel(forceRegenerate ? "Regenerating claim questions..." : "Generating claim questions...");
    setMessage(null);
    try {
      const result = await createClaimVerificationQuestions(
        accessToken,
        profile.id,
        jobResult?.id ?? null,
        forceRegenerate,
      );
      setClaimVerificationResult(result);
      await refreshGeneratedOutputs(accessToken, profile.id);
      setMessage(result.cached ? "Claim questions loaded from cache." : "Claim questions generated.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not generate claim questions.");
    } finally {
      setIsBusy(false);
      setBusyLabel(null);
    }
  }

  async function handleStartMockInterview() {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setBusyLabel("Starting mock interview...");
    setMessage(null);
    try {
      const result = await startMockInterview(accessToken, profile.id, jobResult?.id ?? null, 5);
      setMockInterviewSession(result);
      setMockInterviewEvaluation(null);
      setMockInterviewAnswer("");
      setMessage("Mock interview started.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not start mock interview.");
    } finally {
      setIsBusy(false);
      setBusyLabel(null);
    }
  }

  async function handleSubmitMockAnswer() {
    if (!accessToken || !profile || !mockInterviewSession || !mockInterviewAnswer.trim()) {
      return;
    }

    setIsBusy(true);
    setBusyLabel("Evaluating interview answer...");
    setMessage(null);
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
      setMessage(result.session.status === "completed" ? "Mock interview completed." : "Answer evaluated.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not evaluate answer.");
    } finally {
      setIsBusy(false);
      setBusyLabel(null);
    }
  }

  async function handleCreateOutreachPack() {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setBusyLabel("Generating outreach messages...");
    setMessage(null);
    try {
      const result = await createOutreachMessagePack(accessToken, profile.id, jobResult?.id ?? null);
      setOutreachResult(result);
      await refreshGeneratedOutputs(accessToken, profile.id);
      setMessage(result.cached ? "Outreach messages loaded from cache." : "Outreach messages generated.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not generate outreach messages.");
    } finally {
      setIsBusy(false);
      setBusyLabel(null);
    }
  }

  async function handleCreateCareerTransition() {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setBusyLabel("Generating career transition analysis...");
    setMessage(null);
    try {
      const result = await createCareerTransitionAnalysis(accessToken, profile.id, jobResult?.id ?? null);
      setCareerTransitionResult(result);
      await refreshGeneratedOutputs(accessToken, profile.id);
      setMessage(result.cached ? "Career transition loaded from cache." : "Career transition generated.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not generate career transition analysis.");
    } finally {
      setIsBusy(false);
      setBusyLabel(null);
    }
  }

  async function handleCreateProjectRoadmap(forceRegenerate = false) {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setBusyLabel(forceRegenerate ? "Regenerating project roadmap..." : "Generating project roadmap...");
    setMessage(null);
    try {
      const result = await createProjectRoadmap(
        accessToken,
        profile.id,
        jobResult?.id ?? null,
        forceRegenerate,
      );
      setProjectRoadmapResult(result);
      await refreshGeneratedOutputs(accessToken, profile.id);
      setMessage(result.cached ? "Project roadmap loaded from cache." : "Project roadmap generated.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not generate project roadmap.");
    } finally {
      setIsBusy(false);
      setBusyLabel(null);
    }
  }

  async function handleCreateApplicationMaterials(forceRegenerate = false) {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setBusyLabel(forceRegenerate ? "Regenerating application materials..." : "Generating application materials...");
    setMessage(null);
    try {
      const result = await createApplicationMaterials(
        accessToken,
        profile.id,
        jobResult?.id ?? null,
        forceRegenerate,
      );
      setApplicationMaterialsResult(result);
      await refreshGeneratedOutputs(accessToken, profile.id);
      setMessage(
        result.cached ? "Application materials loaded from cache." : "Application materials generated.",
      );
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not generate application materials.");
    } finally {
      setIsBusy(false);
      setBusyLabel(null);
    }
  }

  async function handleRunDashboard() {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const result = await runReadinessDashboard(accessToken, profile.id, jobResult?.id ?? null);
      setDashboardResult(result);
      setMessage("Readiness dashboard completed.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not run readiness dashboard.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleRunJobMatches() {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setBusyLabel("Retrieving and ranking job matches...");
    setMessage(null);
    try {
      const result = await runJobMatches(accessToken, profile.id, profile.preferred_role, 10);
      setJobMatchResult(result);
      setMessage(result.matches.length ? "Job matches ranked." : "No job references found yet.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not retrieve job matches.");
    } finally {
      setIsBusy(false);
      setBusyLabel(null);
    }
  }

  async function handleRunSkillGap() {
    if (!accessToken || !profile || !jobResult?.id) {
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const result = await runSkillGapAnalysis(accessToken, profile.id, jobResult.id);
      setSkillGapResult(result);
      setMessage("Skill gap analysis completed.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not run skill gap analysis.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleRunReadinessScores() {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const [ats, completeness] = await Promise.all([
        runAtsReadinessAnalysis(accessToken, profile.id),
        runProfileCompletenessAnalysis(accessToken, profile.id),
      ]);
      setAtsResult(ats);
      setCompletenessResult(completeness);
      setMessage("Readiness scores completed.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not run readiness scores.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleRunAnalysis() {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const result = await runResumeQualityAnalysis(accessToken, profile.id);
      setQualityResult(result);
      setMessage("Resume quality analysis completed.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not run resume analysis.");
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <section className="mt-8 max-w-2xl border border-border bg-white p-5">
      <h2 className="text-base font-semibold">Candidate profile</h2>
      {!accessToken ? (
        <p className="mt-2 text-sm text-muted-foreground">Sign in to create a profile and upload a resume.</p>
      ) : (
        <>
          <ProfileSourcesPanel
            githubForm={githubForm}
            githubResult={githubResult}
            isBusy={isBusy}
            linkedInForm={linkedInForm}
            linkedInResult={linkedInResult}
            portfolioForm={portfolioForm}
            portfolioResult={portfolioResult}
            privacySummary={privacySummary}
            profile={profile}
            profileForm={form}
            onAddGitHub={handleAddGitHub}
            onAddLinkedInText={handleAddLinkedInText}
            onAddPortfolio={handleAddPortfolio}
            onCreateProfile={handleCreateProfile}
            onDeleteDocumentsOnly={handleDeleteDocumentsOnly}
            onDeleteProfile={handleDeleteProfile}
            onLoadLatestProfile={handleLoadLatestProfile}
            onLoadPrivacySummary={handleLoadPrivacySummary}
            onUploadLinkedIn={handleUploadLinkedIn}
            onUploadResume={handleUpload}
          />
          {uploadResult ? (
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
              <div className="grid gap-4 pt-2 sm:col-span-2">
                <div>
                  <h3 className="text-sm font-semibold">Analysis</h3>
                  <div className="mt-2 grid gap-2 sm:grid-cols-2">
                    <button className="inline-flex items-center justify-center gap-2 bg-foreground px-4 py-2 text-sm font-medium text-background" disabled={isBusy} type="button" onClick={handleRunAnalysis}>
                      <Gauge aria-hidden="true" className="h-4 w-4" />
                      Resume quality
                    </button>
                    <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={handleRunReadinessScores}>
                      <ClipboardCheck aria-hidden="true" className="h-4 w-4" />
                      Readiness scores
                    </button>
                    <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={handleRunDashboard}>
                      <LayoutDashboard aria-hidden="true" className="h-4 w-4" />
                      Readiness dashboard
                    </button>
                    <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={handleRunJobMatches}>
                      <BriefcaseBusiness aria-hidden="true" className="h-4 w-4" />
                      Job matches
                    </button>
                    <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={handleCreateReport}>
                      <ScrollText aria-hidden="true" className="h-4 w-4" />
                      Basic report
                    </button>
                    <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={handleCreateFullReport}>
                      <ScrollText aria-hidden="true" className="h-4 w-4" />
                      Full report
                    </button>
                  </div>
                </div>
                <div>
                  <h3 className="text-sm font-semibold">Saved outputs</h3>
                  <div className="mt-2 grid gap-2 sm:grid-cols-2">
                    <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isSavedOutputsLoading} type="button" onClick={handleLoadGeneratedOutputs}>
                      <History aria-hidden="true" className="h-4 w-4" />
                      {isSavedOutputsLoading ? "Loading..." : "Load history"}
                    </button>
                  </div>
                </div>
                <div>
                  <h3 className="text-sm font-semibold">AI generation</h3>
                  <div className="mt-2 grid gap-2 sm:grid-cols-2">
                    <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => handleCreateAIInterpretation(false)}>
                      <Sparkles aria-hidden="true" className="h-4 w-4" />
                      AI interpretation
                    </button>
                    <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => handleCreateAIInterpretation(true)}>
                      <Sparkles aria-hidden="true" className="h-4 w-4" />
                      Regenerate interpretation
                    </button>
                    <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => handleCreateRewriteSuggestions(false)}>
                      <ScrollText aria-hidden="true" className="h-4 w-4" />
                      Rewrite suggestions
                    </button>
                    <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => handleCreateRewriteSuggestions(true)}>
                      <ScrollText aria-hidden="true" className="h-4 w-4" />
                      Regenerate rewrites
                    </button>
                    <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => handleCreateTailoringPackage(false)}>
                      <ClipboardCheck aria-hidden="true" className="h-4 w-4" />
                      Tailoring package
                    </button>
                    <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => handleCreateTailoringPackage(true)}>
                      <ClipboardCheck aria-hidden="true" className="h-4 w-4" />
                      Regenerate tailoring
                    </button>
                    <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => handleCreateInterviewPrep(false)}>
                      <MessageSquare aria-hidden="true" className="h-4 w-4" />
                      Interview prep
                    </button>
                    <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => handleCreateInterviewPrep(true)}>
                      <MessageSquare aria-hidden="true" className="h-4 w-4" />
                      Regenerate prep
                    </button>
                    <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => handleCreateClaimVerification(false)}>
                      <MessageSquare aria-hidden="true" className="h-4 w-4" />
                      Claim questions
                    </button>
                    <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => handleCreateClaimVerification(true)}>
                      <MessageSquare aria-hidden="true" className="h-4 w-4" />
                      Regenerate claims
                    </button>
                    <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={handleStartMockInterview}>
                      <MessageSquare aria-hidden="true" className="h-4 w-4" />
                      Mock interview
                    </button>
                    <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={handleCreateOutreachPack}>
                      <MessageSquare aria-hidden="true" className="h-4 w-4" />
                      Outreach messages
                    </button>
                    <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={handleCreateCareerTransition}>
                      <GitCompareArrows aria-hidden="true" className="h-4 w-4" />
                      Career transition
                    </button>
                    <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => handleCreateProjectRoadmap(false)}>
                      <LayoutDashboard aria-hidden="true" className="h-4 w-4" />
                      Project roadmap
                    </button>
                    <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => handleCreateProjectRoadmap(true)}>
                      <LayoutDashboard aria-hidden="true" className="h-4 w-4" />
                      Regenerate roadmap
                    </button>
                    <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => handleCreateApplicationMaterials(false)}>
                      <ScrollText aria-hidden="true" className="h-4 w-4" />
                      Application materials
                    </button>
                    <button className="inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={() => handleCreateApplicationMaterials(true)}>
                      <ScrollText aria-hidden="true" className="h-4 w-4" />
                      Regenerate materials
                    </button>
                  </div>
                </div>
              </div>
            </dl>
          ) : null}
          {qualityResult ? (
            <div className="mt-5 border-t border-border pt-5 text-sm">
              <div className="flex items-baseline gap-3">
                <h3 className="text-base font-semibold">Resume quality</h3>
                <p className="text-2xl font-semibold">{qualityResult.score}</p>
              </div>
              {qualityResult.findings.length ? (
                <ul className="mt-4 space-y-3">
                  {qualityResult.findings.slice(0, 4).map((finding) => (
                    <li key={finding.code} className="border border-border p-3">
                      <p className="font-medium">{finding.title}</p>
                      <p className="mt-1 text-muted-foreground">{finding.recommendation}</p>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-2 text-muted-foreground">No major resume quality issues found.</p>
              )}
            </div>
          ) : null}
          {atsResult || completenessResult ? (
            <div className="mt-5 border-t border-border pt-5 text-sm">
              <h3 className="text-base font-semibold">Readiness scores</h3>
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                {atsResult ? <ScoreCard title="Snipe ATS Readiness" result={atsResult} /> : null}
                {completenessResult ? <ScoreCard title="Profile Completeness" result={completenessResult} /> : null}
              </div>
            </div>
          ) : null}
          {profile ? (
            <form className="mt-5 border-t border-border pt-5" onSubmit={jobForm.handleSubmit(handleCreateJobDescription)}>
              <h3 className="text-base font-semibold">Target job description</h3>
              <textarea className="mt-3 min-h-36 w-full border border-border px-3 py-2 text-sm" placeholder="Paste a target job description here." {...jobForm.register("text")} />
              {jobForm.formState.errors.text ? <p className="mt-2 text-sm text-red-600">{jobForm.formState.errors.text.message}</p> : null}
              <button className="mt-3 inline-flex items-center justify-center gap-2 bg-foreground px-4 py-2 text-sm font-medium text-background" disabled={isBusy} type="submit">
                <BriefcaseBusiness aria-hidden="true" className="h-4 w-4" />
                Analyze job description
              </button>
            </form>
          ) : null}
          {jobResult ? (
            <div className="mt-5 border-t border-border pt-5 text-sm">
              <h3 className="text-base font-semibold">{jobResult.structured.title ?? "Target role"}</h3>
              <dl className="mt-3 grid gap-3 sm:grid-cols-2">
                <JobField label="Company" values={jobResult.structured.company ? [jobResult.structured.company] : []} />
                <JobField label="Seniority" values={jobResult.structured.seniority ? [jobResult.structured.seniority] : []} />
                <JobField label="Required skills" values={jobResult.structured.required_skills} />
                <JobField label="Preferred skills" values={jobResult.structured.preferred_skills} />
                <JobField label="Tools" values={jobResult.structured.tools} />
                <JobField label="ATS keywords" values={jobResult.structured.ats_keywords.slice(0, 8)} />
              </dl>
              <button className="mt-4 inline-flex items-center justify-center gap-2 bg-foreground px-4 py-2 text-sm font-medium text-background" disabled={isBusy || !uploadResult} type="button" onClick={handleRunSkillGap}>
                <GitCompareArrows aria-hidden="true" className="h-4 w-4" />
                Run skill gap analysis
              </button>
            </div>
          ) : null}
          {skillGapResult ? (
            <div className="mt-5 border-t border-border pt-5 text-sm">
              <div className="flex items-baseline gap-3">
                <h3 className="text-base font-semibold">Skill gap</h3>
                <p className="text-2xl font-semibold">{skillGapResult.score}</p>
              </div>
              <div className="mt-3 grid gap-3 sm:grid-cols-2">
                <JobField label="Matched" values={skillGapResult.matched_skills.map((item) => item.skill)} />
                <JobField label="Missing" values={skillGapResult.missing_skills.map((item) => item.skill).slice(0, 8)} />
                <JobField label="Transferable" values={skillGapResult.transferable_skills.map((item) => item.skill)} />
                <JobField label="Not relevant" values={skillGapResult.not_relevant_skills.map((item) => item.skill).slice(0, 8)} />
              </div>
            </div>
          ) : null}
          {dashboardResult ? (
            <div className="mt-5 border-t border-border pt-5 text-sm">
              <div className="flex items-baseline gap-3">
                <h3 className="text-base font-semibold">Readiness dashboard</h3>
                <p className="text-2xl font-semibold">{dashboardResult.scores.overall}</p>
              </div>
              <dl className="mt-3 grid gap-3 sm:grid-cols-2">
                <JobField label="Resume quality" values={[String(dashboardResult.scores.resume_quality)]} />
                <JobField label="ATS readiness" values={[String(dashboardResult.scores.ats_readiness)]} />
                <JobField label="Profile completeness" values={[String(dashboardResult.scores.profile_completeness)]} />
                <JobField label="Skill alignment" values={dashboardResult.scores.skill_alignment === null ? [] : [String(dashboardResult.scores.skill_alignment)]} />
                <JobField label="Primary specialization" values={dashboardResult.interpretation.primary_specialization ? [dashboardResult.interpretation.primary_specialization.name] : []} />
                <JobField label="Estimated seniority" values={dashboardResult.interpretation.estimated_seniority ? [dashboardResult.interpretation.estimated_seniority] : []} />
              </dl>
            </div>
          ) : null}
          {jobMatchResult ? (
            <div className="mt-5 border-t border-border pt-5 text-sm">
              <div className="flex items-baseline gap-3">
                <h3 className="text-base font-semibold">Job matches</h3>
                <p className="text-xs text-muted-foreground">
                  {jobMatchResult.match_count} ranked
                </p>
              </div>
              <div className="mt-4 grid gap-3">
                {jobMatchResult.matches.map((item) => (
                  <div key={`${item.job_reference_id}-${item.citation.chunk_id ?? "chunk"}`} className="border border-border p-3">
                    <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between">
                      <p className="font-medium">{item.title}</p>
                      <p className="text-2xl font-semibold">{item.match_score}</p>
                    </div>
                    <p className="mt-2 text-muted-foreground">{item.explanation}</p>
                    <dl className="mt-3 grid gap-3 sm:grid-cols-2">
                      <JobField label="Recommendation" values={[formatApplyRecommendation(item.apply_recommendation)]} />
                      <JobField label="Skill alignment" values={[String(item.skill_alignment_score)]} />
                      <JobField label="Matched" values={item.matched_skills.slice(0, 8)} />
                      <JobField label="Missing" values={item.missing_skills.slice(0, 8)} />
                      <JobField label="Relevant experience" values={item.relevant_experience.slice(0, 3)} />
                      <JobField label="Concerns" values={item.concerns.slice(0, 4)} />
                    </dl>
                    <p className="mt-3 text-xs text-muted-foreground">
                      Source: {item.citation.title}
                      {item.citation.source_url ? ` (${item.citation.source_url})` : ""}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
          {reportResult ? (
            <div className="mt-5 border-t border-border pt-5 text-sm">
              <div className="flex items-baseline gap-3">
                <h3 className="text-base font-semibold">{reportResult.title}</h3>
                <p className="text-2xl font-semibold">{reportResult.readiness.scores.overall}</p>
              </div>
              <p className="mt-2 text-muted-foreground">{reportResult.summary}</p>
              <dl className="mt-3 grid gap-3 sm:grid-cols-2">
                <JobField label="Strengths" values={reportResult.strengths.slice(0, 3)} />
                <JobField label="Improvement areas" values={reportResult.weaknesses.slice(0, 3)} />
                <JobField label="Skill gaps" values={reportResult.skill_gaps.slice(0, 6)} />
              </dl>
              <pre className="mt-4 max-h-72 overflow-auto whitespace-pre-wrap border border-border bg-muted p-3 text-xs text-muted-foreground">
                {reportResult.markdown}
              </pre>
            </div>
          ) : null}
          {fullReportResult ? (
            <div className="mt-5 border-t border-border pt-5 text-sm">
              <div className="flex items-baseline gap-3">
                <h3 className="text-base font-semibold">{fullReportResult.title}</h3>
                <p className="text-xs text-muted-foreground">{fullReportResult.report_version}</p>
              </div>
              <p className="mt-2 text-muted-foreground">{fullReportResult.summary}</p>
              <dl className="mt-3 grid gap-3 sm:grid-cols-2">
                <JobField label="Sections included" values={fullReportResult.sections_included.slice(0, 12)} />
              </dl>
              <button className="mt-4 inline-flex items-center justify-center gap-2 border border-border px-3 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={handleDownloadFullReport}>
                <Download aria-hidden="true" className="h-4 w-4" />
                Download full report
              </button>
              <pre className="mt-4 max-h-96 overflow-auto whitespace-pre-wrap border border-border bg-muted p-3 text-xs text-muted-foreground">
                {fullReportResult.markdown}
              </pre>
            </div>
          ) : null}
          <SavedOutputsPanel
            deletingOutputId={deletingGeneratedOutputId}
            filter={generatedOutputFilter}
            filteredOutputs={filteredGeneratedOutputs}
            isBusy={isBusy}
            isHistoryRefreshing={isHistoryRefreshing}
            isSavedOutputsLoading={isSavedOutputsLoading}
            outputs={generatedOutputs}
            selectedOutput={selectedGeneratedOutput}
            onCopy={handleCopyGeneratedOutput}
            onDelete={handleDeleteGeneratedOutput}
            onDownload={handleDownloadGeneratedOutput}
            onFilterChange={setGeneratedOutputFilter}
            onOpen={handleOpenGeneratedOutput}
          />
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
                <JobField
                  label="Missing evidence"
                  values={tailoringResult.missing_evidence_warnings.slice(0, 4)}
                />
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
                  <JobField
                    label="Missing evidence"
                    values={interviewResult.missing_evidence_warnings.slice(0, 6)}
                  />
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
                        <p className="text-xs uppercase text-muted-foreground">
                          {item.evidence_strength.replace("_", " ")}
                        </p>
                      </div>
                      <p className="mt-2">{item.question}</p>
                      <p className="mt-2 text-muted-foreground">{item.why_it_matters}</p>
                      <JobField label="Evidence to prepare" values={item.evidence_to_prepare} />
                      {item.caution ? (
                        <p className="mt-2 text-muted-foreground">{item.caution}</p>
                      ) : null}
                    </div>
                  ))}
                </div>
              ) : null}
              <dl className="mt-4 grid gap-3">
                <JobField
                  label="Evidence strength notes"
                  values={claimVerificationResult.evidence_strength_notes}
                />
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
                    onChange={(event) => setMockInterviewAnswer(event.target.value)}
                  />
                  <button className="mt-3 inline-flex items-center justify-center gap-2 bg-foreground px-4 py-2 text-sm font-medium text-background" disabled={isBusy || !mockInterviewAnswer.trim()} type="button" onClick={handleSubmitMockAnswer}>
                    <MessageSquare aria-hidden="true" className="h-4 w-4" />
                    Submit answer
                  </button>
                </div>
              ) : (
                <p className="mt-2 text-muted-foreground">
                  Completed {mockInterviewSession.transcript.length} interview turns.
                </p>
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
                <p className="text-xs text-muted-foreground">
                  {outreachResult.cached ? "Cached" : outreachResult.provider}
                </p>
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
                <p className="text-xs text-muted-foreground">
                  {careerTransitionResult.cached ? "Cached" : careerTransitionResult.provider}
                </p>
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
                <p className="text-xs text-muted-foreground">
                  {projectRoadmapResult.cached ? "Cached" : projectRoadmapResult.provider}
                </p>
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
                      {item.missing_evidence_warning ? (
                        <p className="mt-2 text-muted-foreground">{item.missing_evidence_warning}</p>
                      ) : null}
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
                  <JobField
                    label="Missing evidence"
                    values={projectRoadmapResult.missing_evidence_warnings.slice(0, 6)}
                  />
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
          {applicationMaterialsResult ? (
            <div className="mt-5 border-t border-border pt-5 text-sm">
              <div className="flex items-baseline gap-3">
                <h3 className="text-base font-semibold">Application materials</h3>
                <p className="text-xs text-muted-foreground">
                  {applicationMaterialsResult.cached ? "Cached" : applicationMaterialsResult.provider}
                </p>
              </div>
              <p className="mt-2 text-muted-foreground">{applicationMaterialsResult.summary}</p>
              <div className="mt-4 grid gap-3">
                <div className="border border-border p-3">
                  <p className="font-medium">Cover letter</p>
                  <pre className="mt-2 whitespace-pre-wrap text-sm text-muted-foreground">
                    {applicationMaterialsResult.cover_letter}
                  </pre>
                </div>
                <div className="border border-border p-3">
                  <p className="font-medium">Concise cover note</p>
                  <p className="mt-2 text-muted-foreground">{applicationMaterialsResult.concise_cover_note}</p>
                </div>
                <div className="border border-border p-3">
                  <p className="font-medium">Email application</p>
                  <pre className="mt-2 whitespace-pre-wrap text-sm text-muted-foreground">
                    {applicationMaterialsResult.email_application}
                  </pre>
                </div>
              </div>
              <dl className="mt-4 grid gap-3 sm:grid-cols-2">
                <JobField label="Evidence used" values={applicationMaterialsResult.evidence_used} />
                <JobField
                  label="Missing evidence"
                  values={applicationMaterialsResult.missing_evidence_warnings.slice(0, 6)}
                />
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
      )}
      {busyLabel ? <p className="mt-4 text-sm text-muted-foreground">{busyLabel}</p> : null}
      {isSavedOutputsLoading ? <p className="mt-4 text-sm text-muted-foreground">Loading saved outputs...</p> : null}
      {message ? <p className="mt-4 text-sm text-muted-foreground">{message}</p> : null}
    </section>
  );
}
