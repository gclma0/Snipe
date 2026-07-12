create extension if not exists "pgcrypto";

insert into storage.buckets (id, name, public)
values ('candidate-documents', 'candidate-documents', false)
on conflict (id) do update set public = false;

create table if not exists public.candidate_profiles (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  version integer not null default 1,
  career_goal text,
  preferred_role text,
  target_specialization text,
  target_seniority text,
  location_preference text,
  remote_preference text,
  profile_status text not null default 'draft',
  normalized_json jsonb not null default '{}'::jsonb,
  completeness_score numeric(5, 2),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.profile_sources (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references public.candidate_profiles(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  source_type text not null,
  storage_path text,
  original_filename text,
  content_hash text,
  parsed_text_hash text,
  parser_version text,
  status text not null default 'pending',
  retention_policy text not null default 'retain_private',
  delete_after_parsing boolean not null default false,
  created_at timestamptz not null default now(),
  parsed_at timestamptz,
  deleted_at timestamptz
);

create table if not exists public.profile_evidence (
  id uuid primary key default gen_random_uuid(),
  profile_id uuid not null references public.candidate_profiles(id) on delete cascade,
  source_id uuid references public.profile_sources(id) on delete set null,
  fact_type text not null,
  fact_key text,
  excerpt text,
  normalized_value text,
  confidence numeric(5, 2),
  location_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.analyses (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  profile_id uuid not null references public.candidate_profiles(id) on delete cascade,
  analysis_type text not null,
  input_hash text not null,
  profile_version integer not null,
  job_description_id uuid,
  deterministic_version text,
  ai_prompt_version text,
  model_provider text,
  model_name text,
  result_json jsonb not null default '{}'::jsonb,
  score numeric(6, 2),
  status text not null default 'completed',
  created_at timestamptz not null default now()
);

create table if not exists public.generated_outputs (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  profile_id uuid not null references public.candidate_profiles(id) on delete cascade,
  output_type text not null,
  job_description_id uuid,
  input_hash text not null,
  prompt_version text,
  provider text,
  model_name text,
  result_json jsonb not null default '{}'::jsonb,
  result_markdown text,
  evidence_ids uuid[] not null default '{}',
  status text not null default 'completed',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists candidate_profiles_user_id_idx
  on public.candidate_profiles (user_id);

create index if not exists profile_sources_profile_id_idx
  on public.profile_sources (profile_id);

create index if not exists profile_sources_user_id_idx
  on public.profile_sources (user_id);

create index if not exists profile_evidence_profile_id_idx
  on public.profile_evidence (profile_id);

create index if not exists analyses_profile_id_idx
  on public.analyses (profile_id);

create index if not exists analyses_user_input_idx
  on public.analyses (user_id, input_hash);

create index if not exists generated_outputs_profile_id_idx
  on public.generated_outputs (profile_id);

create index if not exists generated_outputs_cache_idx
  on public.generated_outputs (user_id, output_type, input_hash);

alter table public.candidate_profiles enable row level security;
alter table public.profile_sources enable row level security;
alter table public.profile_evidence enable row level security;
alter table public.analyses enable row level security;
alter table public.generated_outputs enable row level security;

create policy "candidate_profiles_select_own"
  on public.candidate_profiles for select
  using (auth.uid() = user_id);

create policy "candidate_profiles_insert_own"
  on public.candidate_profiles for insert
  with check (auth.uid() = user_id);

create policy "candidate_profiles_update_own"
  on public.candidate_profiles for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy "candidate_profiles_delete_own"
  on public.candidate_profiles for delete
  using (auth.uid() = user_id);

create policy "profile_sources_select_own"
  on public.profile_sources for select
  using (auth.uid() = user_id);

create policy "profile_sources_insert_own"
  on public.profile_sources for insert
  with check (auth.uid() = user_id);

create policy "profile_sources_update_own"
  on public.profile_sources for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy "profile_sources_delete_own"
  on public.profile_sources for delete
  using (auth.uid() = user_id);

create policy "profile_evidence_select_own"
  on public.profile_evidence for select
  using (
    exists (
      select 1
      from public.candidate_profiles
      where candidate_profiles.id = profile_evidence.profile_id
        and candidate_profiles.user_id = auth.uid()
    )
  );

create policy "profile_evidence_insert_own"
  on public.profile_evidence for insert
  with check (
    exists (
      select 1
      from public.candidate_profiles
      where candidate_profiles.id = profile_evidence.profile_id
        and candidate_profiles.user_id = auth.uid()
    )
  );

create policy "profile_evidence_update_own"
  on public.profile_evidence for update
  using (
    exists (
      select 1
      from public.candidate_profiles
      where candidate_profiles.id = profile_evidence.profile_id
        and candidate_profiles.user_id = auth.uid()
    )
  );

create policy "profile_evidence_delete_own"
  on public.profile_evidence for delete
  using (
    exists (
      select 1
      from public.candidate_profiles
      where candidate_profiles.id = profile_evidence.profile_id
        and candidate_profiles.user_id = auth.uid()
    )
  );

create policy "analyses_select_own"
  on public.analyses for select
  using (auth.uid() = user_id);

create policy "analyses_insert_own"
  on public.analyses for insert
  with check (auth.uid() = user_id);

create policy "generated_outputs_select_own"
  on public.generated_outputs for select
  using (auth.uid() = user_id);

create policy "generated_outputs_insert_own"
  on public.generated_outputs for insert
  with check (auth.uid() = user_id);

create policy "generated_outputs_update_own"
  on public.generated_outputs for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy "documents_select_own"
  on storage.objects for select
  using (
    bucket_id = 'candidate-documents'
    and auth.uid()::text = (storage.foldername(name))[1]
  );

create policy "documents_insert_own"
  on storage.objects for insert
  with check (
    bucket_id = 'candidate-documents'
    and auth.uid()::text = (storage.foldername(name))[1]
  );

create policy "documents_update_own"
  on storage.objects for update
  using (
    bucket_id = 'candidate-documents'
    and auth.uid()::text = (storage.foldername(name))[1]
  );

create policy "documents_delete_own"
  on storage.objects for delete
  using (
    bucket_id = 'candidate-documents'
    and auth.uid()::text = (storage.foldername(name))[1]
  );
