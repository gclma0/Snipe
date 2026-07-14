import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";

import { App } from "@/App";

const originalFetch = globalThis.fetch;

afterEach(() => {
  cleanup();
  globalThis.fetch = originalFetch;
});

describe("App", () => {
  it("renders the product shell", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: /Snipe/i })).toBeInTheDocument();
    expect(screen.getByText(/Career intelligence workspace/i)).toBeInTheDocument();
    expect(screen.getByText(/evidence-backed candidate profile/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /Supabase authentication/i })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /System diagnostics/i })).toBeInTheDocument();
  });

  it("loads non-secret system diagnostics on request", async () => {
    const user = userEvent.setup();
    const fetchCalls: string[] = [];
    globalThis.fetch = async (input) => {
      fetchCalls.push(String(input));
      if (String(input).endsWith("/usage/events")) {
        return new Response(JSON.stringify({ accepted: true, event_name: "system_diagnostics_checked" }), {
          status: 202,
          headers: { "Content-Type": "application/json" },
        });
      }
      if (String(input).endsWith("/health")) {
        return new Response(
          JSON.stringify({
            status: "ok",
            service: "Snipe API",
            version: "0.1.0",
            environment: "test",
          }),
          {
            status: 200,
            headers: {
              "Content-Type": "application/json",
              "X-Request-ID": "req-health-123",
              "X-Process-Time-ms": "1.25",
            },
          },
        );
      }
      return new Response(
        JSON.stringify({
          provider: "local_template",
          model_name: "local-template-v1",
          mode: "local_template",
          configured: true,
          requires_api_key: false,
          api_key_configured: false,
          base_url_configured: false,
          timeout_seconds: 30,
          issues: [],
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      );
    };

    render(<App />);

    await user.click(screen.getByRole("button", { name: /Check status/i }));

    expect(await screen.findByText("Provider configuration is ready.")).toBeInTheDocument();
    expect(screen.getByText("Backend health is ok.")).toBeInTheDocument();
    expect(screen.getByText("req-health-123")).toBeInTheDocument();
    expect(screen.getAllByText("local_template").length).toBeGreaterThan(0);
    expect(screen.queryByText(/api key value/i)).not.toBeInTheDocument();
    expect(fetchCalls).toContain("http://localhost:8000/api/v1/usage/events");
  });

  it("shows backend request IDs on API errors", async () => {
    const user = userEvent.setup();
    globalThis.fetch = async () =>
      new Response(JSON.stringify({ detail: "Provider configuration failed." }), {
        status: 500,
        headers: {
          "Content-Type": "application/json",
          "X-Request-ID": "req-test-123",
        },
      });

    render(<App />);

    await user.click(screen.getByRole("button", { name: /Check status/i }));

    expect(await screen.findByText("Provider configuration failed. Request ID: req-test-123")).toBeInTheDocument();
  });

  it("runs an unauthenticated production smoke test from the system panel", async () => {
    const user = userEvent.setup();
    const fetchCalls: string[] = [];
    globalThis.fetch = async (input) => {
      fetchCalls.push(String(input));
      if (String(input).endsWith("/health")) {
        return new Response(
          JSON.stringify({
            status: "ok",
            service: "Snipe API",
            version: "0.1.0",
            environment: "production",
          }),
          {
            status: 200,
            headers: {
              "Content-Type": "application/json",
              "X-Request-ID": "req-smoke-123",
              "X-Process-Time-ms": "2.50",
            },
          },
        );
      }
      if (String(input).endsWith("/usage/events")) {
        return new Response(JSON.stringify({ accepted: true, event_name: "production_smoke_test_ran" }), {
          status: 202,
          headers: { "Content-Type": "application/json" },
        });
      }
      return new Response(
        JSON.stringify({
          provider: "openai_compatible",
          model_name: "free-model",
          mode: "external",
          configured: true,
          requires_api_key: true,
          api_key_configured: true,
          base_url_configured: true,
          timeout_seconds: 30,
          issues: [],
        }),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        },
      );
    };

    render(<App />);

    await user.click(screen.getByRole("button", { name: /Run smoke test/i }));

    expect(await screen.findByText("Smoke test result")).toBeInTheDocument();
    expect(screen.getByText("Backend API")).toBeInTheDocument();
    expect(screen.getAllByText(/req-smoke-123/i).length).toBeGreaterThan(0);
    expect(screen.getByText("AI provider")).toBeInTheDocument();
    expect(screen.getByText("Supabase frontend")).toBeInTheDocument();
    expect(screen.getByText("Supabase session")).toBeInTheDocument();
    expect(screen.getByText("Sign in to test authenticated backend connectivity.")).toBeInTheDocument();
    expect(fetchCalls).toContain("http://localhost:8000/api/v1/usage/events");
  });
});
