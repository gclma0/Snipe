import re
from hashlib import sha256

from pydantic import BaseModel, Field

from app.integrations.portfolio import PortfolioPage
from app.profile.schemas import EvidenceCandidate

ANALYSIS_VERSION = "portfolio-analysis-v1"

TECHNICAL_TERMS = {
    "api",
    "automation",
    "backend",
    "cloud",
    "data",
    "design system",
    "frontend",
    "javascript",
    "python",
    "react",
    "sql",
    "testing",
    "typescript",
    "ux",
}

NON_TECHNICAL_TERMS = {
    "brand",
    "campaign",
    "case study",
    "client",
    "content",
    "copywriting",
    "customer",
    "marketing",
    "operations",
    "portfolio",
    "sales",
    "strategy",
}

PROJECT_TERMS = {"case study", "project", "work", "portfolio", "selected work", "results"}
CONTACT_TERMS = {"contact", "email", "book", "hire", "schedule", "consultation"}


class PortfolioAnalysisResult(BaseModel):
    analysis_version: str = ANALYSIS_VERSION
    url: str
    title: str | None = None
    description: str | None = None
    text_length: int = Field(ge=0)
    link_count: int = Field(ge=0)
    technical_signals: list[str] = Field(default_factory=list)
    non_technical_signals: list[str] = Field(default_factory=list)
    project_signal_count: int = Field(ge=0)
    contact_signal_count: int = Field(ge=0)
    summary_excerpt: str
    signals: dict[str, bool] = Field(default_factory=dict)


def analyze_portfolio_page(page: PortfolioPage) -> PortfolioAnalysisResult:
    haystack = f"{page.title or ''} {page.description or ''} {page.text}".lower()
    technical = _find_terms(haystack, TECHNICAL_TERMS)
    non_technical = _find_terms(haystack, NON_TECHNICAL_TERMS)
    project_count = sum(_contains_term(haystack, term) for term in PROJECT_TERMS)
    contact_count = sum(_contains_term(haystack, term) for term in CONTACT_TERMS)
    return PortfolioAnalysisResult(
        url=page.final_url,
        title=page.title,
        description=page.description,
        text_length=len(page.text),
        link_count=len(page.links),
        technical_signals=technical,
        non_technical_signals=non_technical,
        project_signal_count=project_count,
        contact_signal_count=contact_count,
        summary_excerpt=_excerpt(page.description or page.text, limit=500),
        signals={
            "has_title": bool(page.title),
            "has_description": bool(page.description),
            "has_project_signals": project_count > 0,
            "has_contact_signals": contact_count > 0,
            "has_technical_signals": bool(technical),
            "has_non_technical_signals": bool(non_technical),
        },
    )


def portfolio_evidence(
    *,
    profile_id: str,
    source_id: str | None,
    analysis: PortfolioAnalysisResult,
) -> list[EvidenceCandidate]:
    evidence: list[EvidenceCandidate] = []
    for signal in analysis.technical_signals:
        evidence.append(_evidence(profile_id, source_id, "portfolio_skill", signal, 0.7))
    for signal in analysis.non_technical_signals:
        evidence.append(_evidence(profile_id, source_id, "portfolio_signal", signal, 0.65))
    if analysis.summary_excerpt:
        evidence.append(
            EvidenceCandidate(
                fact_type="portfolio_summary",
                fact_key=_stable_key(analysis.url),
                excerpt=analysis.summary_excerpt,
                normalized_value=analysis.title or analysis.url,
                confidence=0.65,
                location_json={
                    "source": "portfolio",
                    "profile_id": profile_id,
                    "source_id": source_id,
                },
            )
        )
    return evidence


def _evidence(
    profile_id: str,
    source_id: str | None,
    fact_type: str,
    value: str,
    confidence: float,
) -> EvidenceCandidate:
    return EvidenceCandidate(
        fact_type=fact_type,
        fact_key=_stable_key(value),
        excerpt=f"Portfolio page includes {value}.",
        normalized_value=value,
        confidence=confidence,
        location_json={"source": "portfolio", "profile_id": profile_id, "source_id": source_id},
    )


def _find_terms(text: str, terms: set[str]) -> list[str]:
    return sorted(term for term in terms if _contains_term(text, term))


def _contains_term(text: str, term: str) -> bool:
    return bool(re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", text))


def _excerpt(value: str, limit: int = 500) -> str:
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact
    return f"{compact[: limit - 3].rstrip()}..."


def _stable_key(value: str) -> str:
    return sha256(value.lower().strip().encode("utf-8")).hexdigest()[:16]
