import { zodResolver } from "@hookform/resolvers/zod";
import { LogIn, LogOut, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { isSupabaseConfigured } from "@/lib/env";
import { supabase } from "@/lib/supabase";

const signInSchema = z.object({
  email: z.string().email("Enter a valid email address."),
  password: z.string().min(6, "Password must be at least 6 characters."),
});

type SignInValues = z.infer<typeof signInSchema>;

export function AuthPanel() {
  const [email, setEmail] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const form = useForm<SignInValues>({
    resolver: zodResolver(signInSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  useEffect(() => {
    if (!supabase) {
      return undefined;
    }

    supabase.auth.getSession().then(({ data }) => {
      setEmail(data.session?.user.email ?? null);
    });

    const { data } = supabase.auth.onAuthStateChange((_event, session) => {
      setEmail(session?.user.email ?? null);
    });

    return () => data.subscription.unsubscribe();
  }, []);

  if (!isSupabaseConfigured || !supabase) {
    return (
      <section className="mt-10 border-l-4 border-primary bg-muted px-5 py-4">
        <div className="flex items-start gap-3">
          <ShieldCheck aria-hidden="true" className="mt-0.5 h-5 w-5 text-primary" />
          <div>
            <h2 className="text-base font-semibold">Authentication is ready to configure</h2>
            <p className="mt-1 text-sm leading-6 text-muted-foreground">
              Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY to enable Supabase sign-in.
            </p>
          </div>
        </div>
      </section>
    );
  }

  async function handleSignIn(values: SignInValues) {
    if (!supabase) {
      return;
    }

    setMessage(null);
    const { error } = await supabase.auth.signInWithPassword(values);
    setMessage(error ? error.message : "Signed in.");
  }

  async function handleSignOut() {
    if (!supabase) {
      return;
    }

    await supabase.auth.signOut();
    setMessage("Signed out.");
  }

  return (
    <section className="mt-10 max-w-md border border-border bg-white p-5">
      <h2 className="text-base font-semibold">Supabase authentication</h2>
      {email ? (
        <div className="mt-4">
          <p className="text-sm text-muted-foreground">{email}</p>
          <button className="mt-4 inline-flex items-center gap-2 bg-foreground px-4 py-2 text-sm font-medium text-background" onClick={handleSignOut}>
            <LogOut aria-hidden="true" className="h-4 w-4" />
            Sign out
          </button>
        </div>
      ) : (
        <form className="mt-4 space-y-4" onSubmit={form.handleSubmit(handleSignIn)}>
          <label className="block text-sm font-medium">
            Email
            <input className="mt-1 w-full border border-border px-3 py-2" type="email" {...form.register("email")} />
          </label>
          {form.formState.errors.email ? (
            <p className="text-sm text-red-600">{form.formState.errors.email.message}</p>
          ) : null}
          <label className="block text-sm font-medium">
            Password
            <input className="mt-1 w-full border border-border px-3 py-2" type="password" {...form.register("password")} />
          </label>
          {form.formState.errors.password ? (
            <p className="text-sm text-red-600">{form.formState.errors.password.message}</p>
          ) : null}
          <button className="inline-flex items-center gap-2 bg-foreground px-4 py-2 text-sm font-medium text-background" type="submit">
            <LogIn aria-hidden="true" className="h-4 w-4" />
            Sign in
          </button>
        </form>
      )}
      {message ? <p className="mt-4 text-sm text-muted-foreground">{message}</p> : null}
    </section>
  );
}
