from pydantic import BaseModel, Field


class StructuredJobDescription(BaseModel):
    parser_version: str
    title: str | None = None
    company: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    experience_requirements: list[str] = Field(default_factory=list)
    seniority: str | None = None
    ats_keywords: list[str] = Field(default_factory=list)
