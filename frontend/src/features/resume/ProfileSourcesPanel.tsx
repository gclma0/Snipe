import { Download, FileUp, Github, History, Linkedin, LinkIcon, Plus, ScrollText, Trash2 } from "lucide-react";
import { ChangeEvent } from "react";
import { UseFormReturn } from "react-hook-form";

import { JobField } from "@/features/resume/resumeDisplay";
import {
  GitHubValues,
  LinkedInValues,
  PortfolioValues,
  ProfileValues,
} from "@/features/resume/resumeWorkflowForms";
import {
  CandidateProfile,
  GitHubSourceResult,
  LinkedInSourceResult,
  PortfolioSourceResult,
  PrivacyDataSummaryResult,
  PrivacyEvent,
} from "@/lib/api";

type ProfileSourcesPanelProps = {
  profile: CandidateProfile | null;
  profileForm: UseFormReturn<ProfileValues>;
  githubForm: UseFormReturn<GitHubValues>;
  portfolioForm: UseFormReturn<PortfolioValues>;
  linkedInForm: UseFormReturn<LinkedInValues>;
  githubResult: GitHubSourceResult | null;
  portfolioResult: PortfolioSourceResult | null;
  linkedInResult: LinkedInSourceResult | null;
  privacySummary: PrivacyDataSummaryResult | null;
  privacyEvents: PrivacyEvent[];
  deleteResumeAfterParsing: boolean;
  deleteLinkedInAfterParsing: boolean;
  isBusy: boolean;
  onCreateProfile: (values: ProfileValues) => void;
  onLoadLatestProfile: () => void;
  onUploadResume: (event: ChangeEvent<HTMLInputElement>) => void;
  onDeleteResumeAfterParsingChange: (value: boolean) => void;
  onDeleteProfile: () => void;
  onLoadPrivacySummary: () => void;
  onExportProfileData: () => void;
  onLoadPrivacyEvents: () => void;
  onDeleteDocumentsOnly: () => void;
  onAddGitHub: (values: GitHubValues) => void;
  onAddPortfolio: (values: PortfolioValues) => void;
  onAddLinkedInText: (values: LinkedInValues) => void;
  onUploadLinkedIn: (event: ChangeEvent<HTMLInputElement>) => void;
  onDeleteLinkedInAfterParsingChange: (value: boolean) => void;
};

export function ProfileSourcesPanel({
  profile,
  profileForm,
  githubForm,
  portfolioForm,
  linkedInForm,
  githubResult,
  portfolioResult,
  linkedInResult,
  privacySummary,
  privacyEvents,
  deleteResumeAfterParsing,
  deleteLinkedInAfterParsing,
  isBusy,
  onCreateProfile,
  onLoadLatestProfile,
  onUploadResume,
  onDeleteResumeAfterParsingChange,
  onDeleteProfile,
  onLoadPrivacySummary,
  onExportProfileData,
  onLoadPrivacyEvents,
  onDeleteDocumentsOnly,
  onAddGitHub,
  onAddPortfolio,
  onAddLinkedInText,
  onUploadLinkedIn,
  onDeleteLinkedInAfterParsingChange,
}: ProfileSourcesPanelProps) {
  return (
    <>
      <form className="mt-4 grid gap-4 sm:grid-cols-2" onSubmit={profileForm.handleSubmit(onCreateProfile)}>
        <label className="block text-sm font-medium">
          Career goal
          <input className="mt-1 w-full border border-border px-3 py-2" {...profileForm.register("career_goal")} />
        </label>
        <label className="block text-sm font-medium">
          Preferred role
          <input className="mt-1 w-full border border-border px-3 py-2" placeholder="QA Automation Engineer" {...profileForm.register("preferred_role")} />
        </label>
        <button className="inline-flex items-center justify-center gap-2 bg-foreground px-4 py-2 text-sm font-medium text-background sm:col-span-2" disabled={isBusy} type="submit">
          <Plus aria-hidden="true" className="h-4 w-4" />
          Create profile
        </button>
      </form>
      <button className="mt-3 inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={onLoadLatestProfile}>
        <History aria-hidden="true" className="h-4 w-4" />
        Load latest profile
      </button>
      {profileForm.formState.errors.career_goal ? <p className="mt-2 text-sm text-red-600">{profileForm.formState.errors.career_goal.message}</p> : null}
      {profileForm.formState.errors.preferred_role ? <p className="mt-2 text-sm text-red-600">{profileForm.formState.errors.preferred_role.message}</p> : null}
      {profile ? (
        <div className="mt-5 border-t border-border pt-5">
          <p className="text-sm text-muted-foreground">Profile ready for {profile.preferred_role}.</p>
          <label className="mt-4 inline-flex cursor-pointer items-center gap-2 bg-primary px-4 py-2 text-sm font-medium text-primary-foreground">
            <FileUp aria-hidden="true" className="h-4 w-4" />
            Upload resume
            <input className="sr-only" type="file" accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" onChange={onUploadResume} />
          </label>
          <label className="ml-3 mt-4 inline-flex items-center gap-2 text-sm text-muted-foreground">
            <input
              checked={deleteResumeAfterParsing}
              className="h-4 w-4"
              disabled={isBusy}
              type="checkbox"
              onChange={(event) => onDeleteResumeAfterParsingChange(event.target.checked)}
            />
            Delete resume file after parsing
          </label>
          <button className="ml-3 mt-4 inline-flex items-center justify-center gap-2 border border-red-200 px-4 py-2 text-sm font-medium text-red-700" disabled={isBusy} type="button" onClick={onDeleteProfile}>
            <Trash2 aria-hidden="true" className="h-4 w-4" />
            Delete profile data
          </button>
          <button className="ml-3 mt-4 inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={onLoadPrivacySummary}>
            <ScrollText aria-hidden="true" className="h-4 w-4" />
            Data summary
          </button>
          <button className="ml-3 mt-4 inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={onExportProfileData}>
            <Download aria-hidden="true" className="h-4 w-4" />
            Export data
          </button>
          <button className="ml-3 mt-4 inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={onLoadPrivacyEvents}>
            <History aria-hidden="true" className="h-4 w-4" />
            Privacy events
          </button>
          <button className="ml-3 mt-4 inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium" disabled={isBusy} type="button" onClick={onDeleteDocumentsOnly}>
            <Trash2 aria-hidden="true" className="h-4 w-4" />
            Delete documents only
          </button>
          {privacySummary ? (
            <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">
              <JobField label="Stored documents" values={[String(privacySummary.stored_document_count)]} />
              <JobField label="Saved outputs" values={[String(privacySummary.generated_output_count)]} />
              <JobField label="Privacy events" values={[String(privacySummary.privacy_event_count)]} />
              <JobField label="Retention" values={[privacySummary.retention_policy]} />
            </dl>
          ) : null}
          {privacyEvents.length ? (
            <div className="mt-4 grid gap-3 text-sm">
              <h3 className="text-base font-semibold">Privacy event history</h3>
              {privacyEvents.map((event) => (
                <div key={event.id ?? `${event.event_type}-${event.created_at}`} className="border border-border p-3">
                  <p className="font-medium">{event.event_type.split("_").join(" ")}</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {event.created_at ? new Date(event.created_at).toLocaleString() : "Time unavailable"}
                  </p>
                  <pre className="mt-2 overflow-auto whitespace-pre-wrap text-xs text-muted-foreground">
                    {JSON.stringify(event.metadata, null, 2)}
                  </pre>
                </div>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}
      {profile ? (
        <form className="mt-5 border-t border-border pt-5" onSubmit={githubForm.handleSubmit(onAddGitHub)}>
          <h3 className="text-base font-semibold">Optional GitHub source</h3>
          <div className="mt-3 flex flex-col gap-3 sm:flex-row">
            <input className="w-full border border-border px-3 py-2 text-sm" placeholder="octocat or https://github.com/octocat" {...githubForm.register("username_or_url")} />
            <button className="inline-flex items-center justify-center gap-2 bg-foreground px-4 py-2 text-sm font-medium text-background" disabled={isBusy} type="submit">
              <Github aria-hidden="true" className="h-4 w-4" />
              Analyze GitHub
            </button>
          </div>
          {githubForm.formState.errors.username_or_url ? <p className="mt-2 text-sm text-red-600">{githubForm.formState.errors.username_or_url.message}</p> : null}
        </form>
      ) : null}
      {githubResult ? (
        <div className="mt-5 border-t border-border pt-5 text-sm">
          <h3 className="text-base font-semibold">GitHub analysis</h3>
          <dl className="mt-3 grid gap-3 sm:grid-cols-2">
            <JobField label="Username" values={[githubResult.username]} />
            <JobField label="Languages" values={githubResult.primary_languages} />
            <JobField label="Repositories" values={[String(githubResult.analyzed_repository_count)]} />
            <JobField label="README signals" values={[String(githubResult.readme_repository_count)]} />
            <JobField label="Test signals" values={[String(githubResult.test_signal_count)]} />
            <JobField label="CI signals" values={[String(githubResult.ci_signal_count)]} />
            <JobField label="Notable repositories" values={githubResult.notable_repositories.slice(0, 4)} />
          </dl>
        </div>
      ) : null}
      {profile ? (
        <form className="mt-5 border-t border-border pt-5" onSubmit={portfolioForm.handleSubmit(onAddPortfolio)}>
          <h3 className="text-base font-semibold">Optional portfolio source</h3>
          <div className="mt-3 flex flex-col gap-3 sm:flex-row">
            <input className="w-full border border-border px-3 py-2 text-sm" placeholder="https://your-portfolio.com" {...portfolioForm.register("url")} />
            <button className="inline-flex items-center justify-center gap-2 bg-foreground px-4 py-2 text-sm font-medium text-background" disabled={isBusy} type="submit">
              <LinkIcon aria-hidden="true" className="h-4 w-4" />
              Analyze portfolio
            </button>
          </div>
          {portfolioForm.formState.errors.url ? <p className="mt-2 text-sm text-red-600">{portfolioForm.formState.errors.url.message}</p> : null}
        </form>
      ) : null}
      {portfolioResult ? (
        <div className="mt-5 border-t border-border pt-5 text-sm">
          <h3 className="text-base font-semibold">Portfolio analysis</h3>
          <dl className="mt-3 grid gap-3 sm:grid-cols-2">
            <JobField label="Title" values={portfolioResult.title ? [portfolioResult.title] : []} />
            <JobField label="Technical signals" values={portfolioResult.technical_signals} />
            <JobField label="Non-technical signals" values={portfolioResult.non_technical_signals} />
            <JobField label="Project signals" values={[String(portfolioResult.project_signal_count)]} />
            <JobField label="Contact signals" values={[String(portfolioResult.contact_signal_count)]} />
            <JobField label="Evidence records" values={[String(portfolioResult.evidence_count)]} />
          </dl>
        </div>
      ) : null}
      {profile ? (
        <form className="mt-5 border-t border-border pt-5" onSubmit={linkedInForm.handleSubmit(onAddLinkedInText)}>
          <h3 className="text-base font-semibold">Optional LinkedIn source</h3>
          <textarea className="mt-3 min-h-32 w-full border border-border px-3 py-2 text-sm" placeholder="Paste LinkedIn profile text or export content. Direct LinkedIn scraping is not supported." {...linkedInForm.register("text")} />
          {linkedInForm.formState.errors.text ? <p className="mt-2 text-sm text-red-600">{linkedInForm.formState.errors.text.message}</p> : null}
          <div className="mt-3 flex flex-col gap-3 sm:flex-row">
            <button className="inline-flex items-center justify-center gap-2 bg-foreground px-4 py-2 text-sm font-medium text-background" disabled={isBusy} type="submit">
              <Linkedin aria-hidden="true" className="h-4 w-4" />
              Analyze pasted text
            </button>
            <label className="inline-flex cursor-pointer items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium">
              <FileUp aria-hidden="true" className="h-4 w-4" />
              Upload PDF/DOCX
              <input className="sr-only" type="file" accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" onChange={onUploadLinkedIn} />
            </label>
            <label className="inline-flex items-center gap-2 text-sm text-muted-foreground">
              <input
                checked={deleteLinkedInAfterParsing}
                className="h-4 w-4"
                disabled={isBusy}
                type="checkbox"
                onChange={(event) => onDeleteLinkedInAfterParsingChange(event.target.checked)}
              />
              Delete LinkedIn file after parsing
            </label>
          </div>
        </form>
      ) : null}
      {linkedInResult ? (
        <div className="mt-5 border-t border-border pt-5 text-sm">
          <h3 className="text-base font-semibold">LinkedIn analysis</h3>
          <dl className="mt-3 grid gap-3 sm:grid-cols-2">
            <JobField label="Headline" values={linkedInResult.headline ? [linkedInResult.headline] : []} />
            <JobField label="Source type" values={[linkedInResult.source_type]} />
            <JobField label="Skill signals" values={linkedInResult.skill_signals} />
            <JobField label="Experience items" values={[String(linkedInResult.experience_count)]} />
            <JobField label="Evidence records" values={[String(linkedInResult.evidence_count)]} />
            <JobField label="Profile version" values={[String(linkedInResult.profile_version ?? "Pending")]} />
          </dl>
        </div>
      ) : null}
    </>
  );
}
