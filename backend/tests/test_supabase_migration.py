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
