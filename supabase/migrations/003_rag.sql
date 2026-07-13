create extension if not exists "vector";

create table if not exists public.rag_documents (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null,
  source_type text not null,
  source_url text,
  content_hash text not null,
  metadata jsonb not null default '{}'::jsonb,
  embedding_model text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.rag_chunks (
  id uuid primary key default gen_random_uuid(),
  document_id uuid not null references public.rag_documents(id) on delete cascade,
  user_id uuid not null references auth.users(id) on delete cascade,
  chunk_index integer not null,
  content text not null,
  token_count integer not null,
  embedding vector(64) not null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists rag_documents_user_id_idx
  on public.rag_documents (user_id);

create index if not exists rag_documents_user_hash_idx
  on public.rag_documents (user_id, content_hash);

create index if not exists rag_documents_source_type_idx
  on public.rag_documents (source_type);

create index if not exists rag_chunks_document_id_idx
  on public.rag_chunks (document_id);

create index if not exists rag_chunks_user_id_idx
  on public.rag_chunks (user_id);

create index if not exists rag_chunks_embedding_idx
  on public.rag_chunks
  using ivfflat (embedding vector_cosine_ops)
  with (lists = 100);

alter table public.rag_documents enable row level security;
alter table public.rag_chunks enable row level security;

create policy "rag_documents_select_own"
  on public.rag_documents for select
  using (auth.uid() = user_id);

create policy "rag_documents_insert_own"
  on public.rag_documents for insert
  with check (auth.uid() = user_id);

create policy "rag_documents_update_own"
  on public.rag_documents for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy "rag_documents_delete_own"
  on public.rag_documents for delete
  using (auth.uid() = user_id);

create policy "rag_chunks_select_own"
  on public.rag_chunks for select
  using (auth.uid() = user_id);

create policy "rag_chunks_insert_own"
  on public.rag_chunks for insert
  with check (auth.uid() = user_id);

create policy "rag_chunks_update_own"
  on public.rag_chunks for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

create policy "rag_chunks_delete_own"
  on public.rag_chunks for delete
  using (auth.uid() = user_id);

create or replace function public.match_rag_chunks(
  match_user_id uuid,
  query_embedding vector(64),
  source_types text[] default '{}',
  match_count integer default 5
)
returns table (
  document_id uuid,
  chunk_id uuid,
  title text,
  source_type text,
  source_url text,
  chunk_index integer,
  content text,
  score double precision,
  metadata jsonb
)
language sql
stable
as $$
  select
    d.id as document_id,
    c.id as chunk_id,
    d.title,
    d.source_type,
    d.source_url,
    c.chunk_index,
    c.content,
    greatest(0, 1 - (c.embedding <=> query_embedding)) as score,
    c.metadata || jsonb_build_object('document_metadata', d.metadata) as metadata
  from public.rag_chunks c
  join public.rag_documents d on d.id = c.document_id
  where c.user_id = match_user_id
    and d.user_id = match_user_id
    and (
      coalesce(array_length(source_types, 1), 0) = 0
      or d.source_type = any(source_types)
    )
  order by c.embedding <=> query_embedding
  limit least(match_count, 20);
$$;
