create table if not exists public.privacy_events (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  profile_id uuid references public.candidate_profiles(id) on delete set null,
  event_type text not null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists privacy_events_user_id_idx
  on public.privacy_events (user_id);

create index if not exists privacy_events_profile_id_idx
  on public.privacy_events (profile_id);

create index if not exists privacy_events_created_at_idx
  on public.privacy_events (created_at desc);

alter table public.privacy_events enable row level security;

create policy "privacy_events_select_own"
  on public.privacy_events for select
  using (auth.uid() = user_id);

create policy "privacy_events_insert_own"
  on public.privacy_events for insert
  with check (auth.uid() = user_id);
