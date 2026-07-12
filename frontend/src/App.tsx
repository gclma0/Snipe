import { Activity } from "lucide-react";

import { AuthPanel } from "@/features/auth/AuthPanel";

export function App() {
  return (
    <main className="min-h-screen bg-background text-foreground">
      <section className="mx-auto flex min-h-screen max-w-5xl flex-col justify-center px-6 py-12">
        <div className="max-w-3xl">
          <div className="mb-6 inline-flex h-10 w-10 items-center justify-center rounded-md border border-border bg-muted text-primary">
            <Activity aria-hidden="true" className="h-5 w-5" />
          </div>
          <p className="mb-3 text-sm font-medium uppercase tracking-wide text-muted-foreground">
            Milestone 2 scaffold
          </p>
          <h1 className="text-4xl font-semibold tracking-normal sm:text-5xl">
            AI Career Intelligence Platform
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-muted-foreground">
            Frontend tooling is ready. Product workflows begin in later milestones after
            authentication, storage, and the normalized candidate profile are in place.
          </p>
          <AuthPanel />
        </div>
      </section>
    </main>
  );
}
