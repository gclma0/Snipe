import { useState } from "react";

import {
  RagDocumentResult,
  RagDocumentSummary,
  RagSearchResult,
  RagSourceType,
  createRagDocument,
  deleteRagDocument,
  listRagDocuments,
  replaceRagDocument,
  searchJobRagReferences,
  searchRagReferences,
} from "@/lib/api";

type UseRagReferencesParams = {
  accessToken: string | null;
  onBusyChange: (isBusy: boolean) => void;
  onMessage: (message: string | null) => void;
};

export function useRagReferences({
  accessToken,
  onBusyChange,
  onMessage,
}: UseRagReferencesParams) {
  const [ragDocumentResult, setRagDocumentResult] = useState<RagDocumentResult | null>(null);
  const [ragDocuments, setRagDocuments] = useState<RagDocumentSummary[]>([]);
  const [editingRagDocument, setEditingRagDocument] = useState<RagDocumentSummary | null>(null);
  const [ragSearchResult, setRagSearchResult] = useState<RagSearchResult | null>(null);
  const [jobRagSearchResult, setJobRagSearchResult] = useState<RagSearchResult | null>(null);
  const [deletingRagDocumentId, setDeletingRagDocumentId] = useState<string | null>(null);
  const [ragTitle, setRagTitle] = useState("");
  const [ragSourceType, setRagSourceType] = useState<RagSourceType>("job_listing");
  const [ragSourceUrl, setRagSourceUrl] = useState("");
  const [ragText, setRagText] = useState("");
  const [ragQuery, setRagQuery] = useState("");
  const [ragLimit, setRagLimit] = useState(5);
  const [ragSearchSourceTypes, setRagSearchSourceTypes] = useState<RagSourceType[]>([]);

  async function handleIngestRagReference() {
    if (!accessToken) {
      return;
    }

    if (!ragTitle.trim() || ragText.trim().length < 100) {
      onMessage("Reference title and at least 100 characters of text are required.");
      return;
    }

    onBusyChange(true);
    onMessage(null);
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
      onMessage("Reference added to the library.");
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not add reference.");
    } finally {
      onBusyChange(false);
    }
  }

  async function handleLoadRagDocuments() {
    if (!accessToken) {
      return;
    }

    onBusyChange(true);
    onMessage(null);
    try {
      const documents = await listRagDocuments(accessToken);
      setRagDocuments(documents);
      onMessage(documents.length ? "References loaded." : "No saved references found yet.");
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not load references.");
    } finally {
      onBusyChange(false);
    }
  }

  async function handleDeleteRagDocument(documentId: string) {
    if (!accessToken) {
      return;
    }

    setDeletingRagDocumentId(documentId);
    onBusyChange(true);
    onMessage(null);
    try {
      const result = await deleteRagDocument(accessToken, documentId);
      setRagDocuments((current) => current.filter((item) => item.document_id !== result.document_id));
      onMessage("Reference deleted.");
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not delete reference.");
    } finally {
      setDeletingRagDocumentId(null);
      onBusyChange(false);
    }
  }

  function handleEditRagDocument(document: RagDocumentSummary) {
    setEditingRagDocument(document);
    setRagTitle(document.title);
    setRagSourceType(document.source_type);
    setRagSourceUrl(document.source_url ?? "");
    setRagText("");
    onMessage("Paste the updated reference text, then replace the selected reference.");
  }

  function handleCancelEditRagDocument() {
    setEditingRagDocument(null);
    onMessage("Reference edit canceled.");
  }

  async function handleReplaceRagDocument() {
    if (!accessToken || !editingRagDocument) {
      return;
    }

    if (!ragTitle.trim() || ragText.trim().length < 100) {
      onMessage("Reference title and at least 100 characters of replacement text are required.");
      return;
    }

    onBusyChange(true);
    onMessage(null);
    try {
      const result = await replaceRagDocument(accessToken, editingRagDocument.document_id, {
        title: ragTitle.trim(),
        source_type: ragSourceType,
        source_url: ragSourceUrl.trim() || null,
        text: ragText.trim(),
      });
      setRagDocumentResult(result);
      const documents = await listRagDocuments(accessToken);
      setRagDocuments(documents);
      setEditingRagDocument(null);
      onMessage("Reference replaced.");
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not replace reference.");
    } finally {
      onBusyChange(false);
    }
  }

  async function handleSearchRagReferences() {
    if (!accessToken) {
      return;
    }

    if (ragQuery.trim().length < 2) {
      onMessage("Enter at least 2 characters to search references.");
      return;
    }

    onBusyChange(true);
    onMessage(null);
    try {
      const result = await searchRagReferences(accessToken, {
        query: ragQuery.trim(),
        source_types: ragSearchSourceTypes,
        limit: ragLimit,
      });
      setRagSearchResult(result);
      onMessage(result.citations.length ? "References searched." : "No matching references found.");
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not search references.");
    } finally {
      onBusyChange(false);
    }
  }

  async function handleSearchJobRagReferences() {
    if (!accessToken) {
      return;
    }

    if (ragQuery.trim().length < 2) {
      onMessage("Enter at least 2 characters to search job references.");
      return;
    }

    onBusyChange(true);
    onMessage(null);
    try {
      const result = await searchJobRagReferences(accessToken, {
        query: ragQuery.trim(),
        limit: ragLimit,
      });
      setJobRagSearchResult(result);
      onMessage(result.citations.length ? "Job references searched." : "No matching job references found.");
    } catch (error) {
      onMessage(error instanceof Error ? error.message : "Could not search job references.");
    } finally {
      onBusyChange(false);
    }
  }

  return {
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
  };
}
