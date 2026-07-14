import { env } from "@/lib/env";

const SESSION_STORAGE_KEY = "snipe_anonymous_session_id";
let memorySessionId: string | null = null;

export type UsageMetadata = Record<string, string | number | boolean | null | undefined>;

export function trackUsageEvent(
  eventName: string,
  surface: string,
  metadata: UsageMetadata = {},
) {
  const payload = {
    anonymous_session_id: getAnonymousSessionId(),
    event_name: eventName,
    surface,
    metadata: compactMetadata(metadata),
    path: typeof window === "undefined" ? null : window.location.pathname,
  };

  void fetch(`${env.apiBaseUrl}/usage/events`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  }).catch(() => undefined);
}

export function getAnonymousSessionId() {
  if (memorySessionId) {
    writeStoredSessionId(memorySessionId);
    return memorySessionId;
  }

  const stored = readStoredSessionId();
  if (stored) {
    memorySessionId = stored;
    return stored;
  }

  memorySessionId = createSessionId();
  writeStoredSessionId(memorySessionId);
  return memorySessionId;
}

function readStoredSessionId() {
  try {
    return window.sessionStorage.getItem(SESSION_STORAGE_KEY);
  } catch {
    return null;
  }
}

function writeStoredSessionId(sessionId: string) {
  try {
    window.sessionStorage.setItem(SESSION_STORAGE_KEY, sessionId);
  } catch {
    // Session storage can be unavailable in private or restricted browser modes.
  }
}

function createSessionId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `session-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

function compactMetadata(metadata: UsageMetadata) {
  return Object.fromEntries(
    Object.entries(metadata).filter((entry): entry is [string, string | number | boolean | null] => {
      const value = entry[1];
      return value === null || ["boolean", "number", "string"].includes(typeof value);
    }),
  );
}
