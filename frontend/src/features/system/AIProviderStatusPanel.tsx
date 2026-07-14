import { Activity, RefreshCw } from "lucide-react";
import { useState } from "react";

import {
  getAIProviderStatus,
  getBackendHealthStatus,
  getUsageSummary,
  listProfiles,
  type AIProviderStatus,
  type BackendHealthStatus,
  type UsageSummary,
} from "@/lib/api";
import { isSupabaseConfigured } from "@/lib/env";
import { supabase } from "@/lib/supabase";
import { trackUsageEvent } from "@/lib/usage";

type SmokeCheck = {
  name: string;
  status: "passed" | "warning" | "failed";
  detail: string;
};

type AIProviderStatusPanelProps = {
  accessToken?: string | null;
};

export function AIProviderStatusPanel({ accessToken = null }: AIProviderStatusPanelProps) {
  const [backendStatus, setBackendStatus] = useState<BackendHealthStatus | null>(null);
  const [status, setStatus] = useState<AIProviderStatus | null>(null);
  const [smokeChecks, setSmokeChecks] = useState<SmokeCheck[]>([]);
  const [usageSummary, setUsageSummary] = useState<UsageSummary | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSmokeTesting, setIsSmokeTesting] = useState(false);
  const [isLoadingUsage, setIsLoadingUsage] = useState(false);

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

  async function handleRunSmokeTest() {
    setIsSmokeTesting(true);
    setMessage(null);
    const checks: SmokeCheck[] = [];
    try {
      const backend = await getBackendHealthStatus();
      setBackendStatus(backend);
      checks.push({
        name: "Backend API",
        status: backend.status === "ok" ? "passed" : "failed",
        detail: `Service ${backend.service} responded with request ID ${backend.request_id || "not returned"}.`,
      });

      const provider = await getAIProviderStatus();
      setStatus(provider);
      checks.push({
        name: "AI provider",
        status: provider.configured ? "passed" : "warning",
        detail: provider.configured ? "Provider configuration is ready." : provider.issues.join(" "),
      });

      checks.push({
        name: "Supabase frontend",
        status: isSupabaseConfigured && supabase ? "passed" : "failed",
        detail: isSupabaseConfigured && supabase ? "Supabase URL and anon key are configured." : "Supabase frontend environment values are missing.",
      });

      const session = supabase ? await supabase.auth.getSession() : null;
      const hasSession = Boolean(session?.data.session?.access_token || accessToken);
      checks.push({
        name: "Supabase session",
        status: hasSession ? "passed" : "warning",
        detail: hasSession ? "A browser auth session is available." : "Sign in to test authenticated backend connectivity.",
      });

      if (accessToken) {
        const profiles = await listProfiles(accessToken);
        checks.push({
          name: "Authenticated backend",
          status: "passed",
          detail: `Authenticated profile list returned ${profiles.length} profile${profiles.length === 1 ? "" : "s"}.`,
        });
      }

      trackUsageEvent("production_smoke_test_ran", "system_panel", {
        backend_status: backend.status,
        ai_provider_configured: provider.configured,
        authenticated: Boolean(accessToken),
      });
    } catch (error) {
      checks.push({
        name: "Smoke test",
        status: "failed",
        detail: error instanceof Error ? error.message : "Smoke test failed.",
      });
    } finally {
      setSmokeChecks(checks);
      setIsSmokeTesting(false);
    }
  }

  async function handleLoadUsageSummary() {
    if (!accessToken) {
      setMessage("Sign in as an admin to load usage summary.");
      return;
    }

    setIsLoadingUsage(true);
    setMessage(null);
    try {
      const summary = await getUsageSummary(accessToken, 7);
      setUsageSummary(summary);
      trackUsageEvent("usage_summary_loaded", "system_panel", {
        days: summary.days,
        total_events: summary.total_events,
      });
    } catch (error) {
      setUsageSummary(null);
      setMessage(error instanceof Error ? error.message : "Could not load usage summary.");
    } finally {
      setIsLoadingUsage(false);
    }
  }

  return (
    <section className="mt-6 border border-border bg-white p-4 text-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-base font-semibold">System diagnostics</h2>
          <p className="mt-1 text-muted-foreground">Check backend health and the configured generation provider without exposing secrets.</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            className="inline-flex items-center justify-center gap-2 border border-border px-3 py-2 text-sm font-medium"
            disabled={isLoading || isSmokeTesting || isLoadingUsage}
            type="button"
            onClick={handleCheckStatus}
          >
            <RefreshCw aria-hidden="true" className="h-4 w-4" />
            {isLoading ? "Checking..." : "Check status"}
          </button>
          <button
            className="inline-flex items-center justify-center gap-2 bg-foreground px-3 py-2 text-sm font-medium text-background"
            disabled={isLoading || isSmokeTesting || isLoadingUsage}
            type="button"
            onClick={handleRunSmokeTest}
          >
            <Activity aria-hidden="true" className="h-4 w-4" />
            {isSmokeTesting ? "Running..." : "Run smoke test"}
          </button>
          <button
            className="inline-flex items-center justify-center gap-2 border border-border px-3 py-2 text-sm font-medium"
            disabled={isLoading || isSmokeTesting || isLoadingUsage}
            type="button"
            onClick={handleLoadUsageSummary}
          >
            <Activity aria-hidden="true" className="h-4 w-4" />
            {isLoadingUsage ? "Loading..." : "Load usage summary"}
          </button>
        </div>
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
      {smokeChecks.length ? (
        <div className="mt-4 border-t border-border pt-4">
          <h3 className="font-semibold">Smoke test result</h3>
          <div className="mt-3 grid gap-2">
            {smokeChecks.map((check) => (
              <div key={check.name} className="border border-border p-3">
                <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                  <p className="font-medium">{check.name}</p>
                  <p className={statusClassName(check.status)}>{check.status}</p>
                </div>
                <p className="mt-1 text-muted-foreground">{check.detail}</p>
              </div>
            ))}
          </div>
        </div>
      ) : null}
      {usageSummary ? (
        <div className="mt-4 border-t border-border pt-4">
          <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
            <h3 className="font-semibold">Usage summary</h3>
            <p className="text-muted-foreground">Last {usageSummary.days} days</p>
          </div>
          <p className="mt-2 text-muted-foreground">{usageSummary.total_events} aggregate events recorded.</p>
          <div className="mt-3 grid gap-4 sm:grid-cols-2">
            <UsageCountList title="Events" counts={usageSummary.event_counts} />
            <UsageCountList title="Surfaces" counts={usageSummary.surface_counts} />
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

function statusClassName(status: SmokeCheck["status"]) {
  if (status === "passed") {
    return "font-medium text-green-700";
  }
  if (status === "warning") {
    return "font-medium text-yellow-700";
  }
  return "font-medium text-red-700";
}

function UsageCountList({ title, counts }: { title: string; counts: { name: string; count: number }[] }) {
  return (
    <div>
      <h4 className="font-medium">{title}</h4>
      {counts.length ? (
        <ul className="mt-2 space-y-2">
          {counts.slice(0, 5).map((item) => (
            <li key={item.name} className="flex items-center justify-between gap-3 border border-border px-3 py-2">
              <span className="break-all text-muted-foreground">{item.name}</span>
              <span className="font-medium">{item.count}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-2 text-muted-foreground">No aggregate events recorded yet.</p>
      )}
    </div>
  );
}
