import { useState } from "react";

import { SavedOutputsPanel } from "@/features/resume/SavedOutputsPanel";
import { ProfileSourcesPanel } from "@/features/resume/ProfileSourcesPanel";
import { RagReferencePanel } from "@/features/resume/RagReferencePanel";
import { JobAnalysisResults, ReadinessResults, ReportResults } from "@/features/resume/ResumeAnalysisResults";
import { AIResultsPanel } from "@/features/resume/AIResultsPanel";
import { ResumeUploadSummary } from "@/features/resume/ResumeUploadSummary";
import { TargetJobForm } from "@/features/resume/TargetJobForm";
import {
  GitHubValues,
  LinkedInValues,
  PortfolioValues,
  ProfileValues,
} from "@/features/resume/resumeWorkflowForms";
import { useAIGeneration } from "@/features/resume/useAIGeneration";
import { useGeneratedOutputs } from "@/features/resume/useGeneratedOutputs";
import { useJobTargets } from "@/features/resume/useJobTargets";
import { usePrivacyControls } from "@/features/resume/usePrivacyControls";
import { useRagReferences } from "@/features/resume/useRagReferences";
import { useResumeWorkflowDerivedState } from "@/features/resume/useResumeWorkflowDerivedState";
import { useResumeWorkflowForms } from "@/features/resume/useResumeWorkflowForms";
import {
  CandidateProfile,
  DeterministicScoreResult,
  GitHubSourceResult,
  ApplicationMaterialsResult,
  InterviewPrepResult,
  LinkedInSourceResult,
  PortfolioSourceResult,
  ReadinessDashboardResult,
  ResumeQualityResult,
  ResumeTailoringPackageResult,
  ResumeUploadResult,
  SkillGapResult,
  addGitHubSource,
  addLinkedInTextSource,
  addPortfolioSource,
  createProfile,
  deleteProfileData,
  listProfiles,
  runAtsReadinessAnalysis,
  runProfileCompletenessAnalysis,
  runReadinessDashboard,
  runResumeQualityAnalysis,
  runSkillGapAnalysis,
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
  const [githubResult, setGithubResult] = useState<GitHubSourceResult | null>(null);
  const [portfolioResult, setPortfolioResult] = useState<PortfolioSourceResult | null>(null);
  const [linkedInResult, setLinkedInResult] = useState<LinkedInSourceResult | null>(null);
  const [skillGapResult, setSkillGapResult] = useState<SkillGapResult | null>(null);
  const [dashboardResult, setDashboardResult] = useState<ReadinessDashboardResult | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isBusy, setIsBusy] = useState(false);
  const [busyLabel, setBusyLabel] = useState<string | null>(null);
  const [deleteResumeAfterParsing, setDeleteResumeAfterParsing] = useState(false);
  const [deleteLinkedInAfterParsing, setDeleteLinkedInAfterParsing] = useState(false);
  const {
    profileForm: form,
    jobForm,
    githubForm,
    portfolioForm,
    linkedInForm,
  } = useResumeWorkflowForms();
  const {
    clearSelectedGeneratedOutput,
    deletingGeneratedOutputId,
    generatedOutputFilter,
    generatedOutputs,
    handleCopyGeneratedOutput,
    handleDeleteGeneratedOutput,
    handleDownloadGeneratedOutput,
    handleLoadGeneratedOutputs,
    handleOpenGeneratedOutput,
    isHistoryRefreshing,
    isSavedOutputsLoading,
    loadGeneratedOutputsForProfile,
    refreshGeneratedOutputs,
    resetGeneratedOutputHistory,
    selectedGeneratedOutput,
    setGeneratedOutputFilter,
    setLoadedGeneratedOutputs,
  } = useGeneratedOutputs({
    accessToken,
    profileId: profile?.id ?? null,
    onMessage: setMessage,
  });
  const {
    handleDeleteDocumentsOnly,
    handleExportProfileData,
    handleLoadPrivacyEvents,
    handleLoadPrivacySummary,
    privacyEvents,
    privacySummary,
    resetPrivacyState,
  } = usePrivacyControls({
    accessToken,
    profile,
    onBusyChange: setIsBusy,
    onMessage: setMessage,
  });
  const {
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
  } = useJobTargets({
    accessToken,
    profile,
    onBusyChange: setIsBusy,
    onBusyLabelChange: setBusyLabel,
    onMessage: setMessage,
    onResetTargetDependentResults: resetTargetDependentResults,
    onApplicationMaterialsResult: handleJobApplicationMaterialsResult,
    onInterviewResult: handleJobInterviewResult,
    onTailoringResult: handleJobTailoringResult,
    refreshGeneratedOutputs,
  });
  const {
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
  } = useAIGeneration({
    accessToken,
    profile,
    jobResult,
    onBusyChange: setIsBusy,
    onBusyLabelChange: setBusyLabel,
    onMessage: setMessage,
    refreshGeneratedOutputs,
  });
  const {
    deletingRagDocumentId,
    editingRagDocument,
    handleCancelEditRagDocument,
    handleDeleteRagDocument,
    handleEditRagDocument,
    handleIngestRagReference,
    handleLoadRagDocuments,
    handleReplaceRagDocument,
    handleSearchJobRagReferences,
    handleSearchRagReferences,
    jobRagSearchResult,
    ragDocumentResult,
    ragDocuments,
    ragLimit,
    ragQuery,
    ragSearchResult,
    ragSearchSourceTypes,
    ragSourceType,
    ragSourceUrl,
    ragText,
    ragTitle,
    setRagLimit,
    setRagQuery,
    setRagSearchSourceTypes,
    setRagSourceType,
    setRagSourceUrl,
    setRagText,
    setRagTitle,
  } = useRagReferences({
    accessToken,
    onBusyChange: setIsBusy,
    onMessage: setMessage,
  });
  const { activeTargetLabel, filteredGeneratedOutputs } = useResumeWorkflowDerivedState({
    generatedOutputFilter,
    generatedOutputs,
    jobResult,
  });

  function handleJobApplicationMaterialsResult(result: ApplicationMaterialsResult) {
    setApplicationMaterialsResult(result);
  }

  function handleJobInterviewResult(result: InterviewPrepResult) {
    setInterviewResult(result);
  }

  function handleJobTailoringResult(result: ResumeTailoringPackageResult) {
    setTailoringResult(result);
  }

  function resetOptionalSourceResults() {
    setGithubResult(null);
    setPortfolioResult(null);
    setLinkedInResult(null);
  }

  function resetAnalysisResults() {
    setQualityResult(null);
    setAtsResult(null);
    setCompletenessResult(null);
    setSkillGapResult(null);
    clearJobMatchResult();
    setDashboardResult(null);
    resetReportResults();
  }

  function resetProfileDependentResults() {
    resetAnalysisResults();
    resetOptionalSourceResults();
    resetPrivacyState();
    resetAiResults();
    resetGeneratedOutputHistory();
  }

  function resetTargetDependentResults(options: { clearGeneratedOutputs?: boolean; clearJobMatches?: boolean } = {}) {
    setSkillGapResult(null);
    if (options.clearJobMatches) {
      clearJobMatchResult();
    }
    setDashboardResult(null);
    resetReportResults();
    resetAiResults();
    if (options.clearGeneratedOutputs) {
      resetGeneratedOutputHistory();
      return;
    }
    clearSelectedGeneratedOutput();
  }

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
      clearJobTargetState();
      resetProfileDependentResults();
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

      const outputs = await loadGeneratedOutputsForProfile(accessToken, latestProfile.id);
      const jobs = await loadJobDescriptionsForProfile(accessToken, latestProfile.id);
      setProfile(latestProfile);
      setUploadResult(null);
      setJobResult(null);
      resetProfileDependentResults();
      setLoadedGeneratedOutputs(outputs);
      setLoadedJobDescriptions(jobs);
      setMessage(outputs.length ? "Latest profile and saved outputs loaded." : "Latest profile loaded. No saved outputs found yet.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not load latest profile.");
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
      const result = await uploadLinkedInSource(
        accessToken,
        profile.id,
        file,
        deleteLinkedInAfterParsing,
      );
      setLinkedInResult(result);
      setMessage(
        result.raw_document_retained === false
          ? "LinkedIn upload analyzed and raw file deleted."
          : "LinkedIn upload analyzed.",
      );
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
      const result = await uploadResume(accessToken, profile.id, file, deleteResumeAfterParsing);
      setUploadResult(result);
      resetProfileDependentResults();
      setMessage(
        result.raw_document_retained === false
          ? "Resume parsed and raw file deleted."
          : "Resume uploaded and parsed.",
      );
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
      clearJobTargetState();
      resetProfileDependentResults();
      setMessage("Profile data deleted.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not delete profile data.");
    } finally {
      setIsBusy(false);
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
            deleteLinkedInAfterParsing={deleteLinkedInAfterParsing}
            deleteResumeAfterParsing={deleteResumeAfterParsing}
            portfolioForm={portfolioForm}
            portfolioResult={portfolioResult}
            privacySummary={privacySummary}
            privacyEvents={privacyEvents}
            profile={profile}
            profileForm={form}
            onAddGitHub={handleAddGitHub}
            onAddLinkedInText={handleAddLinkedInText}
            onAddPortfolio={handleAddPortfolio}
            onCreateProfile={handleCreateProfile}
            onDeleteDocumentsOnly={handleDeleteDocumentsOnly}
            onDeleteLinkedInAfterParsingChange={setDeleteLinkedInAfterParsing}
            onDeleteProfile={handleDeleteProfile}
            onDeleteResumeAfterParsingChange={setDeleteResumeAfterParsing}
            onExportProfileData={handleExportProfileData}
            onLoadLatestProfile={handleLoadLatestProfile}
            onLoadPrivacyEvents={handleLoadPrivacyEvents}
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
            onCreateLearningPlan={handleCreateLearningPlan}
            onCreateLinkedInOptimization={handleCreateLinkedInOptimization}
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
            isJobMatchHistoryLoading={isJobMatchHistoryLoading}
            isVisible={Boolean(profile)}
            jobForm={jobForm}
            jobOptions={jobOptions}
            matchLimit={jobMatchLimit}
            matchQuery={jobMatchQuery}
            savedJobMatches={savedJobMatches}
            selectedJobId={jobResult?.id ?? null}
            onCreateJobDescription={handleCreateJobDescription}
            onLoadJobMatchHistory={handleLoadJobMatchHistory}
            onMatchLimitChange={setJobMatchLimit}
            onMatchQueryChange={setJobMatchQuery}
            onOpenSavedJobMatch={handleOpenSavedJobMatch}
            onRunJobMatches={handleRunJobMatches}
            onSelectJobDescription={handleSelectJobDescription}
            onUploadJobDescription={handleUploadJobDescription}
          />
          {profile ? (
            <RagReferencePanel
              deletingDocumentId={deletingRagDocumentId}
              documentResult={ragDocumentResult}
              documents={ragDocuments}
              editingDocument={editingRagDocument}
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
              onCancelEditDocument={handleCancelEditRagDocument}
              onDeleteDocument={handleDeleteRagDocument}
              onEditDocument={handleEditRagDocument}
              onIngest={handleIngestRagReference}
              onJobSearch={handleSearchJobRagReferences}
              onLimitChange={setRagLimit}
              onLoadDocuments={handleLoadRagDocuments}
              onQueryChange={setRagQuery}
              onReplaceDocument={handleReplaceRagDocument}
              onSearch={handleSearchRagReferences}
              onSearchSourceTypesChange={setRagSearchSourceTypes}
              onSourceTypeChange={setRagSourceType}
              onSourceUrlChange={setRagSourceUrl}
              onTextChange={setRagText}
              onTitleChange={setRagTitle}
            />
          ) : null}
          <JobAnalysisResults
            activeJobMatchTargetIds={jobMatchTargetIds}
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
            learningPlanResult={learningPlanResult}
            linkedInOptimizationResult={linkedInOptimizationResult}
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
