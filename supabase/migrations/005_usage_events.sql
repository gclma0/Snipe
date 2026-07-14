create table if not exists public.usage_events (
  id uuid primary key default gen_random_uuid(),
  anonymous_session_id text not null,
  event_name text not null,
  surface text not null,
  metadata jsonb not null default '{}'::jsonb,
  path text,
  created_at timestamptz not null default now()
);

create index if not exists usage_events_created_at_idx
  on public.usage_events (created_at desc);

create index if not exists usage_events_event_name_idx
  on public.usage_events (event_name);

create index if not exists usage_events_surface_idx
  on public.usage_events (surface);

alter table public.usage_events enable row level security;

-- Usage events are written by the backend service role only. No browser-facing
-- anon or authenticated policies are defined because this table is aggregate
-- product telemetry, not user-owned profile data.
