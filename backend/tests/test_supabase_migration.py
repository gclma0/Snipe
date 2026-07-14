from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "supabase"
    / "migrations"
    / "001_initial_auth_storage_schema.sql"
)
JOB_DESCRIPTIONS_MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "supabase"
    / "migrations"
    / "002_job_descriptions.sql"
)
RAG_MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "supabase"
    / "migrations"
    / "003_rag.sql"
)
PRIVACY_EVENTS_MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "supabase"
    / "migrations"
    / "004_privacy_events.sql"
)
USAGE_EVENTS_MIGRATION = (
    Path(__file__).resolve().parents[2]
    / "supabase"
    / "migrations"
    / "005_usage_events.sql"
)


def test_initial_migration_defines_core_tables_and_storage_bucket() -> None:
    sql = MIGRATION.read_text(encoding="utf-8").lower()

    for table in [
        "candidate_profiles",
        "profile_sources",
        "profile_evidence",
        "analyses",
        "generated_outputs",
    ]:
        assert f"create table if not exists public.{table}" in sql

    assert "candidate-documents" in sql
    assert "storage.buckets" in sql


def test_initial_migration_enables_rls_and_owning_user_policies() -> None:
    sql = MIGRATION.read_text(encoding="utf-8").lower()

    for table in [
        "candidate_profiles",
        "profile_sources",
        "profile_evidence",
        "analyses",
        "generated_outputs",
    ]:
        assert f"alter table public.{table} enable row level security" in sql

    assert "auth.uid() = user_id" in sql
    assert "documents_insert_own" in sql
    assert "documents_select_own" in sql


def test_job_descriptions_migration_defines_owned_table_and_rls() -> None:
    sql = JOB_DESCRIPTIONS_MIGRATION.read_text(encoding="utf-8").lower()

    assert "create table if not exists public.job_descriptions" in sql
    assert "structured_json jsonb" in sql
    assert "alter table public.job_descriptions enable row level security" in sql
    assert "job_descriptions_select_own" in sql
    assert "auth.uid() = user_id" in sql


def test_rag_migration_defines_vector_tables_rls_and_match_function() -> None:
    sql = RAG_MIGRATION.read_text(encoding="utf-8").lower()

    assert 'create extension if not exists "vector"' in sql
    assert "create table if not exists public.rag_documents" in sql
    assert "create table if not exists public.rag_chunks" in sql
    assert "embedding vector(64)" in sql
    assert "alter table public.rag_documents enable row level security" in sql
    assert "alter table public.rag_chunks enable row level security" in sql
    assert "rag_documents_select_own" in sql
    assert "rag_chunks_select_own" in sql
    assert "create or replace function public.match_rag_chunks" in sql


def test_privacy_events_migration_defines_audit_table_and_rls() -> None:
    sql = PRIVACY_EVENTS_MIGRATION.read_text(encoding="utf-8").lower()

    assert "create table if not exists public.privacy_events" in sql
    assert "event_type text not null" in sql
    assert "metadata jsonb" in sql
    assert "on delete set null" in sql
    assert "alter table public.privacy_events enable row level security" in sql
    assert "privacy_events_select_own" in sql
    assert "privacy_events_insert_own" in sql
    assert "auth.uid() = user_id" in sql


def test_usage_events_migration_defines_anonymous_telemetry_table_without_user_scope() -> None:
    sql = USAGE_EVENTS_MIGRATION.read_text(encoding="utf-8").lower()

    assert "create table if not exists public.usage_events" in sql
    assert "anonymous_session_id text not null" in sql
    assert "event_name text not null" in sql
    assert "metadata jsonb not null" in sql
    assert "alter table public.usage_events enable row level security" in sql
    assert "user_id" not in sql
    assert "profile_id" not in sql
