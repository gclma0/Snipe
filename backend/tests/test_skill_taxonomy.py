from app.skills.taxonomy import canonical_skill, extract_known_skills


def test_extract_known_skills_covers_technical_and_tool_terms() -> None:
    text = "Built REST API automation with Python, GitHub Actions, PostgreSQL, and Power BI."

    skills = extract_known_skills(text)

    assert {"rest api", "automation", "python", "ci/cd", "sql", "power bi"}.issubset(skills)


def test_extract_known_skills_covers_non_technical_professions() -> None:
    text = (
        "Managed patient care documentation, scheduling, medical billing, "
        "customer service, and conflict resolution."
    )

    skills = extract_known_skills(text)

    assert {
        "patient care",
        "documentation",
        "scheduling",
        "medical billing",
        "customer service",
        "conflict resolution",
    }.issubset(skills)


def test_canonical_skill_normalizes_common_aliases() -> None:
    assert canonical_skill("PostgreSQL") == "sql"
    assert canonical_skill("MS Excel") == "excel"
    assert canonical_skill("Quality Assurance") == "qa testing"
