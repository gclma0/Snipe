import { useState } from "react";

import { downloadJson } from "@/features/resume/generatedOutputFormatting";
import {
  CandidateProfile,
  PrivacyDataSummaryResult,
  PrivacyEvent,
  deleteProfileDocuments,
  exportProfileData,
  getPrivacyDataSummary,
  listPrivacyEvents,
} from "@/lib/api";

type UsePrivacyControlsParams = {
  accessToken: string | null;
  profile: CandidateProfile | null;
  onBusyChange: (isBusy: boolean) => void;
  onMessage: (message: string | null) => void;
};

export function usePrivacyControls({
  accessToken,
  profile,
  onBusyChange,
  onMessage,
}: UsePrivacyControlsParams) {
  const [privacySummary, setPrivacySummary] = useState<PrivacyDataSummaryResult | null>(null);
  const [privacyEvents, setPrivacyEvents] = useState<PrivacyEvent[]>([]);

  function resetPrivacyState() {
    setPrivacySummary(null);
    setPrivacyEvents([]);
  }

  async function loadPrivacySummary() {
    if (!accessToken || !profile) {
      return null;
    }

    const result = await getPrivacyDataSummary(accessToken, profile.id);
    setPrivacySummary(result);
    return result;
  }

  async function handleLoadPrivacySummary() {
    if (!accessToken || !profile) {
      return;
    }

    onBusyChange(true);
    onMessage(null);
    try {
      await loadPrivacySummary();
      onMessage("Privacy summary loaded.");
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not load privacy summary.");
    } finally {
      onBusyChange(false);
    }
  }

  async function handleExportProfileData() {
    if (!accessToken || !profile) {
      return;
    }

    onBusyChange(true);
    onMessage(null);
    try {
      const result = await exportProfileData(accessToken, profile.id);
      downloadJson(`snipe-profile-export-${profile.id}.json`, result);
      setPrivacyEvents(result.privacy_events);
      onMessage("Profile data export generated.");
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not export profile data.");
    } finally {
      onBusyChange(false);
    }
  }

  async function handleLoadPrivacyEvents() {
    if (!accessToken || !profile) {
      return;
    }

    onBusyChange(true);
    onMessage(null);
    try {
      const result = await listPrivacyEvents(accessToken, profile.id);
      setPrivacyEvents(result);
      onMessage(result.length ? "Privacy events loaded." : "No privacy events found yet.");
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not load privacy events.");
    } finally {
      onBusyChange(false);
    }
  }

  async function handleDeleteDocumentsOnly() {
    if (!accessToken || !profile) {
      return;
    }

    onBusyChange(true);
    onMessage(null);
    try {
      const result = await deleteProfileDocuments(accessToken, profile.id);
      await loadPrivacySummary();
      onMessage(`Deleted ${result.deleted_storage_objects} stored document object(s).`);
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not delete stored documents.");
    } finally {
      onBusyChange(false);
    }
  }

  return {
    handleDeleteDocumentsOnly,
    handleExportProfileData,
    handleLoadPrivacyEvents,
    handleLoadPrivacySummary,
    privacyEvents,
    privacySummary,
    resetPrivacyState,
  };
}
