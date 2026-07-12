from pydantic import BaseModel, Field


class ResumeParseResult(BaseModel):
    parser: str
    source_type: str
    text: str
    text_length: int = Field(ge=0)
    page_count: int | None = Field(default=None, ge=0)
    paragraph_count: int | None = Field(default=None, ge=0)
