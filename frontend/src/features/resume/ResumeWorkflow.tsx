import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";

import { SavedOutputsPanel } from "@/features/resume/SavedOutputsPanel";
import { ProfileSourcesPanel } from "@/features/resume/ProfileSourcesPanel";
import { RagReferencePanel } from "@/features/resume/RagReferencePanel";
import { JobAnalysisResults, ReadinessResults, ReportResults } from "@/features/resume/ResumeAnalysisResults";
import { AIResultsPanel } from "@/features/resume/AIResultsPanel";
import { ResumeUploadSummary } from "@/features/resume/ResumeUploadSummary";
import { TargetJobForm } from "@/features/resume/TargetJobForm";
import { exportContentForOutput, fullReportFilename, generatedOutputFilename } from "@/features/resume/generatedOutputFormatting";
import {
  GitHubValues,
  JobDescriptionValues,
  LinkedInValues,
  PortfolioValues,
  ProfileValues,
  githubSchema,
  jobDescriptionSchema,
  linkedInSchema,
  portfolioSchema,
  profileSchema,
} from "@/features/resume/resumeWorkflowForms";
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
  JobMatch,
  JobMatchResult,
  LinkedInSourceResult,
  MockInterviewSession,
  OutreachMessagePack,
  PortfolioSourceResult,
  PrivacyDataSummaryResult,
  RagDocumentResult,
  RagDocumentSummary,
  RagSearchResult,
  RagSourceType,
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
  createRagDocument,
  createResumeRewriteSuggestions,
  createResumeTailoringPackage,
  createProfile,
  deleteGeneratedOutput,
  deleteProfileData,
  deleteProfileDocuments,
  deleteRagDocument,
  getPrivacyDataSummary,
  getGeneratedOutput,
  listGeneratedOutputs,
  listJobDescriptions,
  listProfiles,
  listRagDocuments,
  runAtsReadinessAnalysis,
  runJobMatches,
  runProfileCompletenessAnalysis,
  runReadinessDashboard,
  runResumeQualityAnalysis,
  runSkillGapAnalysis,
  searchJobRagReferences,
  searchRagReferences,
  startMockInterview,
  uploadLinkedInSource,
  uploadResume,
} from "@/lib/api";

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
  const [jobOptions, setJobOptions] = useState<JobDescriptionResult[]>([]);
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
  const [ragDocumentResult, setRagDocumentResult] = useState<RagDocumentResult | null>(null);
  const [ragDocuments, setRagDocuments] = useState<RagDocumentSummary[]>([]);
  const [ragSearchResult, setRagSearchResult] = useState<RagSearchResult | null>(null);
  const [jobRagSearchResult, setJobRagSearchResult] = useState<RagSearchResult | null>(null);
  const [generatedOutputs, setGeneratedOutputs] = useState<GeneratedOutput[]>([]);
  const [generatedOutputFilter, setGeneratedOutputFilter] = useState("all");
  const [selectedGeneratedOutput, setSelectedGeneratedOutput] = useState<GeneratedOutput | null>(null);
  const [deletingGeneratedOutputId, setDeletingGeneratedOutputId] = useState<string | null>(null);
  const [deletingRagDocumentId, setDeletingRagDocumentId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isBusy, setIsBusy] = useState(false);
  const [busyLabel, setBusyLabel] = useState<string | null>(null);
  const [isSavedOutputsLoading, setIsSavedOutputsLoading] = useState(false);
  const [isHistoryRefreshing, setIsHistoryRefreshing] = useState(false);
  const [jobMatchQuery, setJobMatchQuery] = useState("");
  const [jobMatchLimit, setJobMatchLimit] = useState(10);
  const [ragTitle, setRagTitle] = useState("");
  const [ragSourceType, setRagSourceType] = useState<RagSourceType>("job_listing");
  const [ragSourceUrl, setRagSourceUrl] = useState("");
  const [ragText, setRagText] = useState("");
  const [ragQuery, setRagQuery] = useState("");
  const [ragLimit, setRagLimit] = useState(5);
  const [ragSearchSourceTypes, setRagSearchSourceTypes] = useState<RagSourceType[]>([]);
  const activeTargetLabel = jobResult
    ? `${jobResult.structured.title ?? "Target role"}${jobResult.structured.company ? ` at ${jobResult.structured.company}` : ""}`
    : null;
  const filteredGeneratedOutputs =
    generatedOutputFilter === "all"
      ? generatedOutputs
      : generatedOutputFilter === "active_target"
        ? generatedOutputs.filter((item) => Boolean(jobResult?.id) && item.job_description_id === jobResult?.id)
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
      setJobOptions([]);
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
      const jobs = await listJobDescriptions(accessToken, latestProfile.id);
      setProfile(latestProfile);
      setUploadResult(null);
      setQualityResult(null);
      setAtsResult(null);
      setCompletenessResult(null);
      setJobResult(null);
      setJobOptions(jobs);
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
      setJobOptions((current) => [result, ...current.filter((job) => job.id !== result.id)]);
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

  function handleSelectJobDescription(jobId: string) {
    const selected = jobOptions.find((job) => job.id === jobId) ?? null;
    setJobResult(selected);
    setSkillGapResult(null);
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
    setSelectedGeneratedOutput(null);
    setMessage(selected ? "Saved target job selected." : "Target job selection cleared.");
  }

  async function saveJobMatchAsTarget(match: JobMatch) {
    if (!accessToken || !profile) {
      return null;
    }

    if (match.source_excerpt.trim().length < 100) {
      setMessage("This job match does not include enough source text to save as a target job.");
      return null;
    }

    const result = await createJobDescription(accessToken, profile.id, match.source_excerpt);
    setJobResult(result);
    setJobOptions((current) => [result, ...current.filter((job) => job.id !== result.id)]);
    setSkillGapResult(null);
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
    setSelectedGeneratedOutput(null);
    return result;
  }

  async function handleSaveJobMatchAsTarget(match: JobMatch) {
    if (!accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const result = await saveJobMatchAsTarget(match);
      if (result) {
        setMessage("Job match saved as the active target job.");
      }
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not save job match as target.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleSaveJobMatchAndGenerate(
    match: JobMatch,
    outputType: "tailoring" | "interview" | "materials",
  ) {
    if (!accessToken || !profile) {
      return;
    }

    const labels = {
      tailoring: "tailoring package",
      interview: "interview prep",
      materials: "application materials",
    };
    setIsBusy(true);
    setBusyLabel(`Saving match and generating ${labels[outputType]}...`);
    setMessage(null);
    try {
      const targetJob = await saveJobMatchAsTarget(match);
      if (!targetJob?.id) {
        return;
      }
      if (outputType === "tailoring") {
        const result = await createResumeTailoringPackage(accessToken, profile.id, targetJob.id, false);
        setTailoringResult(result);
      } else if (outputType === "interview") {
        const result = await createInterviewPrep(accessToken, profile.id, targetJob.id, false);
        setInterviewResult(result);
      } else {
        const result = await createApplicationMaterials(accessToken, profile.id, targetJob.id, false);
        setApplicationMaterialsResult(result);
      }
      await refreshGeneratedOutputs(accessToken, profile.id);
      setMessage(`Job match saved and ${labels[outputType]} generated.`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : `Could not generate ${labels[outputType]}.`);
    } finally {
      setIsBusy(false);
      setBusyLabel(null);
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
      setJobOptions([]);
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
      const result = await runJobMatches(
        accessToken,
        profile.id,
        jobMatchQuery.trim() || profile.preferred_role,
        jobMatchLimit,
      );
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

  async function handleIngestRagReference() {
    if (!accessToken) {
      return;
    }

    if (!ragTitle.trim() || ragText.trim().length < 100) {
      setMessage("Reference title and at least 100 characters of text are required.");
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const result = await createRagDocument(accessToken, {
        title: ragTitle.trim(),
        source_type: ragSourceType,
        source_url: ragSourceUrl.trim() || null,
        text: ragText.trim(),
      });
      setRagDocumentResult(result);
      setRagQuery((current) => current || result.title);
      const documents = await listRagDocuments(accessToken);
      setRagDocuments(documents);
      setMessage("Reference added to the library.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not add reference.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleLoadRagDocuments() {
    if (!accessToken) {
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const documents = await listRagDocuments(accessToken);
      setRagDocuments(documents);
      setMessage(documents.length ? "References loaded." : "No saved references found yet.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not load references.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleDeleteRagDocument(documentId: string) {
    if (!accessToken) {
      return;
    }

    setDeletingRagDocumentId(documentId);
    setIsBusy(true);
    setMessage(null);
    try {
      const result = await deleteRagDocument(accessToken, documentId);
      setRagDocuments((current) => current.filter((item) => item.document_id !== result.document_id));
      setMessage("Reference deleted.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not delete reference.");
    } finally {
      setDeletingRagDocumentId(null);
      setIsBusy(false);
    }
  }

  async function handleSearchRagReferences() {
    if (!accessToken) {
      return;
    }

    if (ragQuery.trim().length < 2) {
      setMessage("Enter at least 2 characters to search references.");
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const result = await searchRagReferences(accessToken, {
        query: ragQuery.trim(),
        source_types: ragSearchSourceTypes,
        limit: ragLimit,
      });
      setRagSearchResult(result);
      setMessage(result.citations.length ? "References searched." : "No matching references found.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not search references.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleSearchJobRagReferences() {
    if (!accessToken) {
      return;
    }

    if (ragQuery.trim().length < 2) {
      setMessage("Enter at least 2 characters to search job references.");
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const result = await searchJobRagReferences(accessToken, {
        query: ragQuery.trim(),
        limit: ragLimit,
      });
      setJobRagSearchResult(result);
      setMessage(result.citations.length ? "Job references searched." : "No matching job references found.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not search job references.");
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
          <ResumeUploadSummary
            activeTargetLabel={activeTargetLabel}
            isBusy={isBusy}
            isSavedOutputsLoading={isSavedOutputsLoading}
            uploadResult={uploadResult}
            onCreateAIInterpretation={handleCreateAIInterpretation}
            onCreateApplicationMaterials={handleCreateApplicationMaterials}
            onCreateCareerTransition={handleCreateCareerTransition}
            onCreateClaimVerification={handleCreateClaimVerification}
            onCreateFullReport={handleCreateFullReport}
            onCreateInterviewPrep={handleCreateInterviewPrep}
            onCreateOutreachPack={handleCreateOutreachPack}
            onCreateProjectRoadmap={handleCreateProjectRoadmap}
            onCreateReport={handleCreateReport}
            onCreateRewriteSuggestions={handleCreateRewriteSuggestions}
            onCreateTailoringPackage={handleCreateTailoringPackage}
            onLoadGeneratedOutputs={handleLoadGeneratedOutputs}
            onRunAnalysis={handleRunAnalysis}
            onRunDashboard={handleRunDashboard}
            onRunJobMatches={handleRunJobMatches}
            onRunReadinessScores={handleRunReadinessScores}
            onStartMockInterview={handleStartMockInterview}
          />
          <ReadinessResults
            atsResult={atsResult}
            completenessResult={completenessResult}
            qualityResult={qualityResult}
          />
          <TargetJobForm
            isBusy={isBusy}
            isVisible={Boolean(profile)}
            jobForm={jobForm}
            jobOptions={jobOptions}
            matchLimit={jobMatchLimit}
            matchQuery={jobMatchQuery}
            selectedJobId={jobResult?.id ?? null}
            onCreateJobDescription={handleCreateJobDescription}
            onMatchLimitChange={setJobMatchLimit}
            onMatchQueryChange={setJobMatchQuery}
            onRunJobMatches={handleRunJobMatches}
            onSelectJobDescription={handleSelectJobDescription}
          />
          {profile ? (
            <RagReferencePanel
              deletingDocumentId={deletingRagDocumentId}
              documentResult={ragDocumentResult}
              documents={ragDocuments}
              isBusy={isBusy}
              jobSearchResult={jobRagSearchResult}
              limit={ragLimit}
              query={ragQuery}
              searchResult={ragSearchResult}
              searchSourceTypes={ragSearchSourceTypes}
              sourceType={ragSourceType}
              sourceUrl={ragSourceUrl}
              text={ragText}
              title={ragTitle}
              onDeleteDocument={handleDeleteRagDocument}
              onIngest={handleIngestRagReference}
              onJobSearch={handleSearchJobRagReferences}
              onLimitChange={setRagLimit}
              onLoadDocuments={handleLoadRagDocuments}
              onQueryChange={setRagQuery}
              onSearch={handleSearchRagReferences}
              onSearchSourceTypesChange={setRagSearchSourceTypes}
              onSourceTypeChange={setRagSourceType}
              onSourceUrlChange={setRagSourceUrl}
              onTextChange={setRagText}
              onTitleChange={setRagTitle}
            />
          ) : null}
          <JobAnalysisResults
            dashboardResult={dashboardResult}
            hasUploadResult={Boolean(uploadResult)}
            isBusy={isBusy}
            jobMatchResult={jobMatchResult}
            jobResult={jobResult}
            skillGapResult={skillGapResult}
            onGenerateFromJobMatch={handleSaveJobMatchAndGenerate}
            onSaveJobMatchAsTarget={handleSaveJobMatchAsTarget}
            onRunSkillGap={handleRunSkillGap}
          />
          <ReportResults
            fullReportResult={fullReportResult}
            isBusy={isBusy}
            reportResult={reportResult}
            onDownloadFullReport={handleDownloadFullReport}
          />
          <SavedOutputsPanel
            activeTargetId={jobResult?.id ?? null}
            activeTargetLabel={activeTargetLabel}
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
          <AIResultsPanel
            aiInterpretationResult={aiInterpretationResult}
            applicationMaterialsResult={applicationMaterialsResult}
            careerTransitionResult={careerTransitionResult}
            claimVerificationResult={claimVerificationResult}
            interviewResult={interviewResult}
            isBusy={isBusy}
            mockInterviewAnswer={mockInterviewAnswer}
            mockInterviewEvaluation={mockInterviewEvaluation}
            mockInterviewSession={mockInterviewSession}
            outreachResult={outreachResult}
            projectRoadmapResult={projectRoadmapResult}
            rewriteResult={rewriteResult}
            tailoringResult={tailoringResult}
            onMockInterviewAnswerChange={setMockInterviewAnswer}
            onSubmitMockAnswer={handleSubmitMockAnswer}
          />
        </>
      )}
      {busyLabel ? <p className="mt-4 text-sm text-muted-foreground">{busyLabel}</p> : null}
      {isSavedOutputsLoading ? <p className="mt-4 text-sm text-muted-foreground">Loading saved outputs...</p> : null}
      {message ? <p className="mt-4 text-sm text-muted-foreground">{message}</p> : null}
    </section>
  );
}
