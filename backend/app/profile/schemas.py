from pydantic import BaseModel, Field


class EvidenceCandidate(BaseModel):
    fact_type: str
    fact_key: str
    excerpt: str
    normalized_value: str
    confidence: float = Field(ge=0, le=1)
    location_json: dict[str, str | int | float | bool | None] = Field(default_factory=dict)


class NormalizedProfileBuild(BaseModel):
    normalized_json: dict
    evidence: list[EvidenceCandidate]
