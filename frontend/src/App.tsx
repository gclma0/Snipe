import { Activity } from "lucide-react";
import { useCallback, useState } from "react";

import { AuthPanel } from "@/features/auth/AuthPanel";
import { ResumeWorkflow } from "@/features/resume/ResumeWorkflow";
import { AIProviderStatusPanel } from "@/features/system/AIProviderStatusPanel";
import { isAdminEmail } from "@/lib/env";

export function App() {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const handleSessionChange = useCallback((session: { token: string | null; email: string | null }) => {
    setAccessToken(session.token);
    setUserEmail(session.email);
  }, []);
  const handleTokenChange = useCallback((token: string | null) => {
    setAccessToken(token);
  }, []);

  return (
    <main className="min-h-screen bg-background text-foreground">
      <section className="mx-auto flex min-h-screen max-w-5xl flex-col justify-center px-6 py-12">
        <div className="max-w-3xl">
          <div className="mb-6 inline-flex h-10 w-10 items-center justify-center rounded-md border border-border bg-muted text-primary">
            <Activity aria-hidden="true" className="h-5 w-5" />
          </div>
          <p className="mb-3 text-sm font-medium uppercase tracking-wide text-muted-foreground">
            Career intelligence workspace
          </p>
          <h1 className="text-4xl font-semibold tracking-normal sm:text-5xl">
            Snipe
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-muted-foreground">
            Build one evidence-backed candidate profile, compare it against target roles,
            generate tailored career materials, and keep saved outputs reusable without
            resending raw documents.
          </p>
          <AuthPanel onSessionChange={handleSessionChange} onTokenChange={handleTokenChange} />
          {isAdminEmail(userEmail) ? <AIProviderStatusPanel accessToken={accessToken} /> : null}
          <ResumeWorkflow accessToken={accessToken} />
        </div>
      </section>
    </main>
  );
}
