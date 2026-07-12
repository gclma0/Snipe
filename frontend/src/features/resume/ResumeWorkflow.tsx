import { zodResolver } from "@hookform/resolvers/zod";
import { FileUp, Plus } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { CandidateProfile, ResumeUploadResult, createProfile, uploadResume } from "@/lib/api";

const profileSchema = z.object({
  career_goal: z.string().min(1, "Career goal is required.").max(120),
  preferred_role: z.string().min(1, "Preferred role is required.").max(120),
});

type ProfileValues = z.infer<typeof profileSchema>;

type ResumeWorkflowProps = {
  accessToken: string | null;
};

export function ResumeWorkflow({ accessToken }: ResumeWorkflowProps) {
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [uploadResult, setUploadResult] = useState<ResumeUploadResult | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [isBusy, setIsBusy] = useState(false);
  const form = useForm<ProfileValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      career_goal: "Prepare for a target role",
      preferred_role: "",
    },
  });

  async function handleCreateProfile(values: ProfileValues) {
    if (!accessToken) {
      setMessage("Sign in before creating a profile.");
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const created = await createProfile(accessToken, values);
      setProfile(created);
      setUploadResult(null);
      setMessage("Profile created.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not create profile.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file || !accessToken || !profile) {
      return;
    }

    setIsBusy(true);
    setMessage(null);
    try {
      const result = await uploadResume(accessToken, profile.id, file);
      setUploadResult(result);
      setMessage("Resume uploaded and parsed.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Could not upload resume.");
    } finally {
      setIsBusy(false);
      event.target.value = "";
    }
  }

  return (
    <section className="mt-8 max-w-2xl border border-border bg-white p-5">
      <h2 className="text-base font-semibold">Candidate profile</h2>
      {!accessToken ? (
        <p className="mt-2 text-sm text-muted-foreground">Sign in to create a profile and upload a resume.</p>
      ) : (
        <>
          <form className="mt-4 grid gap-4 sm:grid-cols-2" onSubmit={form.handleSubmit(handleCreateProfile)}>
            <label className="block text-sm font-medium">
              Career goal
              <input className="mt-1 w-full border border-border px-3 py-2" {...form.register("career_goal")} />
            </label>
            <label className="block text-sm font-medium">
              Preferred role
              <input className="mt-1 w-full border border-border px-3 py-2" placeholder="QA Automation Engineer" {...form.register("preferred_role")} />
            </label>
            <button className="inline-flex items-center justify-center gap-2 bg-foreground px-4 py-2 text-sm font-medium text-background sm:col-span-2" disabled={isBusy} type="submit">
              <Plus aria-hidden="true" className="h-4 w-4" />
              Create profile
            </button>
          </form>
          {form.formState.errors.career_goal ? <p className="mt-2 text-sm text-red-600">{form.formState.errors.career_goal.message}</p> : null}
          {form.formState.errors.preferred_role ? <p className="mt-2 text-sm text-red-600">{form.formState.errors.preferred_role.message}</p> : null}
          {profile ? (
            <div className="mt-5 border-t border-border pt-5">
              <p className="text-sm text-muted-foreground">Profile ready for {profile.preferred_role}.</p>
              <label className="mt-4 inline-flex cursor-pointer items-center gap-2 bg-primary px-4 py-2 text-sm font-medium text-primary-foreground">
                <FileUp aria-hidden="true" className="h-4 w-4" />
                Upload resume
                <input className="sr-only" type="file" accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" onChange={handleUpload} />
              </label>
            </div>
          ) : null}
          {uploadResult ? (
            <dl className="mt-5 grid gap-3 border-t border-border pt-5 text-sm sm:grid-cols-2">
              <div>
                <dt className="font-medium">File</dt>
                <dd className="text-muted-foreground">{uploadResult.original_filename}</dd>
              </div>
              <div>
                <dt className="font-medium">Status</dt>
                <dd className="text-muted-foreground">{uploadResult.status}</dd>
              </div>
              <div>
                <dt className="font-medium">Source type</dt>
                <dd className="text-muted-foreground">{uploadResult.source_type}</dd>
              </div>
              <div>
                <dt className="font-medium">Text length</dt>
                <dd className="text-muted-foreground">{uploadResult.text_length}</dd>
              </div>
            </dl>
          ) : null}
        </>
      )}
      {message ? <p className="mt-4 text-sm text-muted-foreground">{message}</p> : null}
    </section>
  );
}
