from app.parsing.schemas import ResumeParseResult
from app.profile.contact_extractor import extract_contact
from app.profile.profile_builder import build_normalized_profile
from app.profile.section_detector import detect_sections


def test_extract_contact_finds_email_phone_and_links() -> None:
    contact = extract_contact(
        "Avery Lee\navery@example.com\n(555) 123-4567\nlinkedin.com/in/avery"
    )

    assert contact["emails"] == ["avery@example.com"]
    assert contact["phones"] == ["(555) 123-4567"]
    assert contact["links"] == ["https://linkedin.com/in/avery"]


def test_detect_sections_maps_common_resume_headings() -> None:
    sections = detect_sections(
        """
Summary
Operations manager with vendor coordination experience.
Skills
Excel, budgeting, stakeholder management
Experience
Led monthly planning process.
"""
    )

    assert sections["summary"] == "Operations manager with vendor coordination experience."
    assert "Excel" in sections["skills"]
    assert sections["experience"] == "Led monthly planning process."


def test_build_normalized_profile_supports_non_technical_resume_facts() -> None:
    parsed = ResumeParseResult(
        parser="test-parser",
        source_type="resume_pdf",
        text="""
Jordan Smith
jordan@example.com
Summary
Finance analyst focused on budgeting and stakeholder management.
Skills
Excel, financial modeling, communication
Experience
Built monthly budget reports for leadership.
Education
BS Finance
""",
        text_length=220,
        page_count=1,
    )

    result = build_normalized_profile(parsed=parsed, profile_id="profile-id", source_id="source-id")

    skills = {skill["name"] for skill in result.normalized_json["skills"]}
    fact_types = {item.fact_type for item in result.evidence}
    assert {"budgeting", "communication", "excel", "financial modeling"}.issubset(skills)
    assert result.normalized_json["contact"]["emails"] == ["jordan@example.com"]
    assert "experience_section" in fact_types
    assert "skill" in fact_types


def test_build_normalized_profile_extracts_broader_professional_skills() -> None:
    parsed = ResumeParseResult(
        parser="test-parser",
        source_type="resume_pdf",
        text="""
Taylor Morgan
Summary
Administrative coordinator with scheduling, documentation, vendor management, and data entry.
Skills
Microsoft Office, Google Sheets, customer service, event planning, attention to detail
Experience
Coordinated weekly schedules and maintained compliance documentation.
""",
        text_length=280,
        page_count=1,
    )

    result = build_normalized_profile(parsed=parsed, profile_id="profile-id", source_id="source-id")

    skills = {skill["name"] for skill in result.normalized_json["skills"]}
    assert {
        "administration",
        "attention to detail",
        "customer service",
        "data entry",
        "documentation",
        "event planning",
        "google sheets",
        "microsoft office",
        "scheduling",
        "vendor management",
    }.issubset(skills)
