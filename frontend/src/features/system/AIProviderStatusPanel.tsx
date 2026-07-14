import { Activity, RefreshCw } from "lucide-react";
import { useState } from "react";

import { getAIProviderStatus, type AIProviderStatus } from "@/lib/api";

export function AIProviderStatusPanel() {
  const [status, setStatus] = useState<AIProviderStatus | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function handleCheckStatus() {
    setIsLoading(true);
    setMessage(null);
    try {
      const result = await getAIProviderStatus();
      setStatus(result);
    } catch (error) {
      setStatus(null);
      setMessage(error instanceof Error ? error.message : "Could not load AI provider status.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section className="mt-6 border border-border bg-white p-4 text-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-base font-semibold">AI provider</h2>
          <p className="mt-1 text-muted-foreground">Check the configured generation provider without exposing secrets.</p>
        </div>
        <button
          className="inline-flex items-center justify-center gap-2 border border-border px-3 py-2 text-sm font-medium"
          disabled={isLoading}
          type="button"
          onClick={handleCheckStatus}
        >
          <RefreshCw aria-hidden="true" className="h-4 w-4" />
          {isLoading ? "Checking..." : "Check status"}
        </button>
      </div>
      {status ? (
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <StatusField label="Provider" value={status.provider} />
          <StatusField label="Model" value={status.model_name || "Not configured"} />
          <StatusField label="Mode" value={status.mode} />
          <StatusField label="Timeout" value={`${status.timeout_seconds}s`} />
          <StatusField label="API key" value={status.requires_api_key ? (status.api_key_configured ? "Configured" : "Missing") : "Not required"} />
          <StatusField label="Base URL" value={status.base_url_configured ? "Custom" : "Default"} />
          <div className="sm:col-span-2">
            <div className="flex items-center gap-2">
              <Activity aria-hidden="true" className="h-4 w-4" />
              <p className={status.configured ? "font-medium text-green-700" : "font-medium text-red-700"}>
                {status.configured ? "Provider configuration is ready." : "Provider configuration needs attention."}
              </p>
            </div>
            {status.issues.length ? (
              <ul className="mt-2 list-disc space-y-1 pl-5 text-muted-foreground">
                {status.issues.map((issue) => (
                  <li key={issue}>{issue}</li>
                ))}
              </ul>
            ) : null}
          </div>
        </div>
      ) : null}
      {message ? <p className="mt-3 text-sm text-red-600">{message}</p> : null}
    </section>
  );
}

function StatusField({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="font-medium">{label}</p>
      <p className="mt-1 text-muted-foreground">{value}</p>
    </div>
  );
}
