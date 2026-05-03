from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class ApplicationCreateRequest(BaseModel):
    company: str = Field(min_length=1)
    position: str = Field(min_length=1)
    jd_text: str = ""
    resume_version: str = ""
    status: str = "planned"
    apply_date: date | None = None
    source: str = ""
    notes: str = ""
    match_score: float | None = None
    next_action: str = ""


class ApplicationUpdateRequest(BaseModel):
    company: str | None = None
    position: str | None = None
    jd_text: str | None = None
    resume_version: str | None = None
    status: str | None = None
    apply_date: date | None = None
    source: str | None = None
    notes: str | None = None
    match_score: float | None = None
    next_action: str | None = None


class ApplicationSearchRequest(BaseModel):
    company: str | None = None
    position: str | None = None
    status: str | None = None
    source: str | None = None
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class ApplicationResponse(BaseModel):
    id: int
    company: str
    position: str
    jd_text: str
    resume_version: str
    status: str
    apply_date: date | None
    source: str
    notes: str
    match_score: float | None
    next_action: str
    created_at: datetime
    updated_at: datetime
