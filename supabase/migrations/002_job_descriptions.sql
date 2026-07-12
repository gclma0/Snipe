create table if not exists public.job_descriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  profile_id uuid references public.candidate_profiles(id) on delete cascade,
  title text,
  company text,
  source_type text not null default 'pasted_text',
  input_hash text not null,
  raw_text text not null,
  structured_json jsonb not null default '{}'::jsonb,
  parser_version text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists job_descriptions_user_id_idx
  on public.job_descriptions (user_id);

create index if not exists job_descriptions_profile_id_idx
  on public.job_descriptions (profile_id);

create index if not exists job_descriptions_user_input_hash_idx
  on public.job_descriptions (user_id, input_hash);

alter table public.job_descriptions enable row level security;

create policy "job_descriptions_select_own"
  on public.job_descriptions for select
  using (auth.uid() = user_id);

create policy "job_descriptions_insert_own"
  on public.job_descriptions for insert
  with check (auth.uid() = user_id);

create policy "job_descriptions_update_own"
  on public.job_descriptions for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy "job_descriptions_delete_own"
  on public.job_descriptions for delete
  using (auth.uid() = user_id);
