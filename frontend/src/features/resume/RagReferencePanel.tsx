import { Database, Search } from "lucide-react";

import { RagDocumentResult, RagSearchResult, RagSourceType } from "@/lib/api";

const sourceTypeOptions: { value: RagSourceType; label: string }[] = [
  { value: "job_listing", label: "Job listing" },
  { value: "job_description", label: "Job description" },
  { value: "role_framework", label: "Role framework" },
  { value: "career_guidance", label: "Career guidance" },
];

type RagReferencePanelProps = {
  documentResult: RagDocumentResult | null;
  searchResult: RagSearchResult | null;
  jobSearchResult: RagSearchResult | null;
  isBusy: boolean;
  title: string;
  sourceType: RagSourceType;
  sourceUrl: string;
  text: string;
  query: string;
  limit: number;
  onTitleChange: (value: string) => void;
  onSourceTypeChange: (value: RagSourceType) => void;
  onSourceUrlChange: (value: string) => void;
  onTextChange: (value: string) => void;
  onQueryChange: (value: string) => void;
  onLimitChange: (value: number) => void;
  onIngest: () => void;
  onJobSearch: () => void;
  onSearch: () => void;
};

export function RagReferencePanel({
  documentResult,
  searchResult,
  jobSearchResult,
  isBusy,
  title,
  sourceType,
  sourceUrl,
  text,
  query,
  limit,
  onTitleChange,
  onSourceTypeChange,
  onSourceUrlChange,
  onTextChange,
  onQueryChange,
  onLimitChange,
  onIngest,
  onJobSearch,
  onSearch,
}: RagReferencePanelProps) {
  return (
    <div className="mt-5 border-t border-border pt-5 text-sm">
      <h3 className="text-base font-semibold">Reference library</h3>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <label className="block text-sm font-medium">
          Title
          <input
            className="mt-2 w-full border border-border bg-background px-3 py-2 text-sm"
            disabled={isBusy}
            value={title}
            onChange={(event) => onTitleChange(event.target.value)}
          />
        </label>
        <label className="block text-sm font-medium">
          Source type
          <select
            className="mt-2 w-full border border-border bg-background px-3 py-2 text-sm"
            disabled={isBusy}
            value={sourceType}
            onChange={(event) => onSourceTypeChange(event.target.value as RagSourceType)}
          >
            {sourceTypeOptions.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm font-medium sm:col-span-2">
          Source URL
          <input
            className="mt-2 w-full border border-border bg-background px-3 py-2 text-sm"
            disabled={isBusy}
            type="url"
            value={sourceUrl}
            onChange={(event) => onSourceUrlChange(event.target.value)}
          />
        </label>
        <label className="block text-sm font-medium sm:col-span-2">
          Reference text
          <textarea
            className="mt-2 min-h-36 w-full border border-border bg-background px-3 py-2 text-sm"
            disabled={isBusy}
            value={text}
            onChange={(event) => onTextChange(event.target.value)}
          />
        </label>
      </div>
      <button
        className="mt-3 inline-flex items-center justify-center gap-2 bg-foreground px-4 py-2 text-sm font-medium text-background"
        disabled={isBusy}
        type="button"
        onClick={onIngest}
      >
        <Database aria-hidden="true" className="h-4 w-4" />
        Add reference
      </button>
      {documentResult ? (
        <p className="mt-3 text-muted-foreground">
          Added {documentResult.title} as {documentResult.chunk_count} searchable chunk(s).
        </p>
      ) : null}
      <div className="mt-5 border-t border-border pt-5">
        <h4 className="text-sm font-semibold">Search references</h4>
        <div className="mt-3 grid gap-3 sm:grid-cols-[1fr_9rem]">
          <label className="block text-sm font-medium">
            Query
            <input
              className="mt-2 w-full border border-border bg-background px-3 py-2 text-sm"
              disabled={isBusy}
              value={query}
              onChange={(event) => onQueryChange(event.target.value)}
            />
          </label>
          <label className="block text-sm font-medium">
            Reference results
            <select
              className="mt-2 w-full border border-border bg-background px-3 py-2 text-sm"
              disabled={isBusy}
              value={String(limit)}
              onChange={(event) => onLimitChange(Number(event.target.value))}
            >
              <option value="3">3</option>
              <option value="5">5</option>
              <option value="10">10</option>
              <option value="20">20</option>
            </select>
          </label>
        </div>
        <button
          className="mt-3 inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium"
          disabled={isBusy}
          type="button"
          onClick={onSearch}
        >
          <Search aria-hidden="true" className="h-4 w-4" />
          Search references
        </button>
        <button
          className="ml-0 mt-3 inline-flex items-center justify-center gap-2 border border-border px-4 py-2 text-sm font-medium sm:ml-2"
          disabled={isBusy}
          type="button"
          onClick={onJobSearch}
        >
          <Search aria-hidden="true" className="h-4 w-4" />
          Search job references only
        </button>
      </div>
      {searchResult ? (
        <div className="mt-4">
          <CitationList result={searchResult} />
        </div>
      ) : null}
      {jobSearchResult ? (
        <div className="mt-4 border-t border-border pt-4">
          <h4 className="text-sm font-semibold">Job reference results</h4>
          <CitationList result={jobSearchResult} />
        </div>
      ) : null}
    </div>
  );
}

function CitationList({ result }: { result: RagSearchResult }) {
  if (!result.citations.length) {
    return <p className="mt-3 text-muted-foreground">No matching references found.</p>;
  }

  return (
    <div className="mt-3 grid gap-3">
      {result.citations.map((item) => (
        <div key={`${item.document_id}-${item.chunk_id ?? item.chunk_index}`} className="border border-border p-3">
          <div className="flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between">
            <p className="font-medium">{item.title}</p>
            <p className="text-xs text-muted-foreground">{Math.round(item.score * 100)}%</p>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            {item.source_type}
            {item.source_url ? ` - ${item.source_url}` : ""}
          </p>
          <p className="mt-2 text-muted-foreground">{item.content.slice(0, 360)}</p>
        </div>
      ))}
    </div>
  );
}
