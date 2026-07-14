import { useState } from "react";

import {
  downloadTextFile,
  exportContentForOutput,
  generatedOutputFilename,
} from "@/features/resume/generatedOutputFormatting";
import {
  GeneratedOutput,
  deleteGeneratedOutput,
  getGeneratedOutput,
  listGeneratedOutputs,
} from "@/lib/api";

type UseGeneratedOutputsParams = {
  accessToken: string | null;
  profileId: string | null;
  onMessage: (message: string | null) => void;
};

export function useGeneratedOutputs({
  accessToken,
  profileId,
  onMessage,
}: UseGeneratedOutputsParams) {
  const [generatedOutputs, setGeneratedOutputs] = useState<GeneratedOutput[]>([]);
  const [generatedOutputFilter, setGeneratedOutputFilter] = useState("all");
  const [selectedGeneratedOutput, setSelectedGeneratedOutput] = useState<GeneratedOutput | null>(null);
  const [deletingGeneratedOutputId, setDeletingGeneratedOutputId] = useState<string | null>(null);
  const [isSavedOutputsLoading, setIsSavedOutputsLoading] = useState(false);
  const [isHistoryRefreshing, setIsHistoryRefreshing] = useState(false);

  function resetGeneratedOutputHistory() {
    setGeneratedOutputs([]);
    setGeneratedOutputFilter("all");
    setSelectedGeneratedOutput(null);
  }

  function setLoadedGeneratedOutputs(outputs: GeneratedOutput[]) {
    setGeneratedOutputs(outputs);
    setGeneratedOutputFilter("all");
    setSelectedGeneratedOutput(null);
  }

  function clearSelectedGeneratedOutput() {
    setSelectedGeneratedOutput(null);
  }

  async function loadGeneratedOutputsForProfile(token: string, targetProfileId: string) {
    const result = await listGeneratedOutputs(token, targetProfileId);
    setLoadedGeneratedOutputs(result);
    return result;
  }

  async function handleLoadGeneratedOutputs() {
    if (!accessToken || !profileId) {
      return;
    }

    setIsSavedOutputsLoading(true);
    onMessage(null);
    try {
      const result = await loadGeneratedOutputsForProfile(accessToken, profileId);
      onMessage(result.length ? "Saved outputs loaded." : "No saved outputs found yet.");
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not load saved outputs.");
    } finally {
      setIsSavedOutputsLoading(false);
    }
  }

  async function refreshGeneratedOutputs(token: string, targetProfileId: string) {
    setIsHistoryRefreshing(true);
    try {
      const result = await listGeneratedOutputs(token, targetProfileId);
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
      onMessage("Saved output copied.");
    } catch {
      onMessage("Could not copy saved output.");
    }
  }

  async function handleOpenGeneratedOutput(output: GeneratedOutput) {
    if (!accessToken || !profileId) {
      return;
    }

    setIsSavedOutputsLoading(true);
    onMessage(null);
    try {
      const result = await getGeneratedOutput(accessToken, profileId, output.id);
      setSelectedGeneratedOutput(result);
      setGeneratedOutputs((current) =>
        current.map((item) => (item.id === result.id ? result : item)),
      );
      onMessage("Saved output opened.");
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not open saved output.");
    } finally {
      setIsSavedOutputsLoading(false);
    }
  }

  async function handleDeleteGeneratedOutput(output: GeneratedOutput) {
    if (!accessToken || !profileId) {
      return;
    }

    setDeletingGeneratedOutputId(output.id);
    onMessage(null);
    try {
      await deleteGeneratedOutput(accessToken, profileId, output.id);
      setGeneratedOutputs((current) => current.filter((item) => item.id !== output.id));
      setSelectedGeneratedOutput((current) => (current?.id === output.id ? null : current));
      onMessage("Saved output deleted.");
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not delete saved output.");
    } finally {
      setDeletingGeneratedOutputId(null);
    }
  }

  function handleDownloadGeneratedOutput(output: GeneratedOutput) {
    const content = exportContentForOutput(output);
    downloadTextFile(generatedOutputFilename(output), content, "text/markdown;charset=utf-8");
    onMessage("Saved output downloaded.");
  }

  return {
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
  };
}
