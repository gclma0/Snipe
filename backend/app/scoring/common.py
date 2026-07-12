import json
from hashlib import sha256
from typing import Any, Literal

from pydantic import BaseModel, Field

Severity = Literal["info", "low", "medium", "high"]


class ScoreFinding(BaseModel):
    code: str
    severity: Severity
    title: str
    detail: str
    recommendation: str


class DeterministicScoreResult(BaseModel):
    analysis_type: str
    deterministic_version: str
    score: int = Field(ge=0, le=100)
    findings: list[ScoreFinding]
    checks: dict[str, bool]


def normalized_profile_hash(normalized_profile: dict[str, Any]) -> str:
    encoded = json.dumps(normalized_profile, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def score_from_findings(findings: list[ScoreFinding]) -> int:
    penalties = {"high": 16, "medium": 10, "low": 5, "info": 0}
    return max(0, 100 - sum(penalties[finding.severity] for finding in findings))


def finding(
    code: str,
    severity: Severity,
    title: str,
    detail: str,
    recommendation: str,
) -> ScoreFinding:
    return ScoreFinding(
        code=code,
        severity=severity,
        title=title,
        detail=detail,
        recommendation=recommendation,
    )
