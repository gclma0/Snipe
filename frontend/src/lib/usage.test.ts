import { afterEach, describe, expect, it, vi } from "vitest";

import { getAnonymousSessionId, trackUsageEvent } from "@/lib/usage";

const originalFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = originalFetch;
  window.sessionStorage.clear();
  vi.restoreAllMocks();
});

describe("usage analytics", () => {
  it("reuses one anonymous session id in session storage", () => {
    const first = getAnonymousSessionId();
    const second = getAnonymousSessionId();

    expect(first).toBe(second);
    expect(window.sessionStorage.getItem("snipe_anonymous_session_id")).toBe(first);
  });

  it("posts compact anonymous usage events without blocking callers", () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ accepted: true }), {
        status: 202,
        headers: { "Content-Type": "application/json" },
      }),
    );
    globalThis.fetch = fetchMock;

    trackUsageEvent("ai_provider_checked", "system_panel", {
      configured: true,
      skipped: undefined,
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/usage/events",
      expect.objectContaining({
        method: "POST",
        headers: { "Content-Type": "application/json" },
      }),
    );
    const body = JSON.parse(fetchMock.mock.calls[0][1].body as string);
    expect(body.event_name).toBe("ai_provider_checked");
    expect(body.surface).toBe("system_panel");
    expect(body.metadata).toEqual({ configured: true });
    expect(body.anonymous_session_id).toBeTruthy();
  });
});
