from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ResumeMatchRequest(BaseModel):
    resume_text: str
    jd_text: str


class ResumeMatchResponse(BaseModel):
    overall_score: float
    skill_match_score: float
    project_match_score: float
    keyword_coverage_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    weaknesses: list[str]
    suggestions: list[str]
    analysis_mode: Literal["rules", "llm"] = "rules"


class ResumeRewriteRequest(BaseModel):
    resume_text: str
    project_experience: str
    jd_text: str
    rag_context: list[str] = Field(default_factory=list)


class ResumeRewriteResponse(BaseModel):
    optimized_project_description: str
    bullet_points: list[str]
    skill_keywords: list[str]
    highlight_points: list[str]
    risk_warnings: list[str]
    analysis_mode: Literal["rules", "llm"] = "rules"
