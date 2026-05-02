from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class JDAnalyzeRequest(BaseModel):
    jd_text: str


class JDAnalyzeResponse(BaseModel):
    job_title: str
    job_category: str
    responsibilities: list[str]
    required_skills: list[str]
    bonus_skills: list[str]
    resume_keywords: list[str]
    interview_topics: list[str]
    risk_points: list[str]
    analysis_mode: Literal["rules", "llm"] = "rules"
