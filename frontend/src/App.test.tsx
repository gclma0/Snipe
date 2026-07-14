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
    expect(screen.getByRole("heading", { name: /AI provider/i })).toBeInTheDocument();
  });

  it("loads non-secret AI provider status on request", async () => {
    const user = userEvent.setup();
    globalThis.fetch = async () =>
      new Response(
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

    render(<App />);

    await user.click(screen.getByRole("button", { name: /Check status/i }));

    expect(await screen.findByText("Provider configuration is ready.")).toBeInTheDocument();
    expect(screen.getAllByText("local_template").length).toBeGreaterThan(0);
    expect(screen.queryByText(/api key value/i)).not.toBeInTheDocument();
  });
});
