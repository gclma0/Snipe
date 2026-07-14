import { Activity, RefreshCw } from "lucide-react";
import { useState } from "react";

import { getAIProviderStatus, getBackendHealthStatus, type AIProviderStatus, type BackendHealthStatus } from "@/lib/api";
import { trackUsageEvent } from "@/lib/usage";

export function AIProviderStatusPanel() {
  const [backendStatus, setBackendStatus] = useState<BackendHealthStatus | null>(null);
  const [status, setStatus] = useState<AIProviderStatus | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function handleCheckStatus() {
    setIsLoading(true);
    setMessage(null);
    try {
      const backend = await getBackendHealthStatus();
      const result = await getAIProviderStatus();
      setBackendStatus(backend);
      setStatus(result);
      trackUsageEvent("system_diagnostics_checked", "system_panel", {
        backend_status: backend.status,
        configured: result.configured,
        mode: result.mode,
        provider: result.provider,
      });
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
          <h2 className="text-base font-semibold">System diagnostics</h2>
          <p className="mt-1 text-muted-foreground">Check backend health and the configured generation provider without exposing secrets.</p>
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
      {backendStatus ? (
        <div className="mt-4 border-b border-border pb-4">
          <div className="flex items-center gap-2">
            <Activity aria-hidden="true" className="h-4 w-4" />
            <p className="font-medium text-green-700">Backend health is ok.</p>
          </div>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            <StatusField label="Service" value={backendStatus.service} />
            <StatusField label="Version" value={backendStatus.version} />
            <StatusField label="Environment" value={backendStatus.environment} />
            <StatusField label="Request ID" value={backendStatus.request_id || "Not returned"} />
            <StatusField label="Process time" value={backendStatus.process_time_ms ? `${backendStatus.process_time_ms}ms` : "Not returned"} />
          </div>
        </div>
      ) : null}
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
