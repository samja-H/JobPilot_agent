from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class InterviewQuestionRequest(BaseModel):
    resume_text: str
    project_experience: str
    jd_text: str
    rag_context: list[str] = Field(default_factory=list)


class InterviewQuestionResponse(BaseModel):
    technical_questions: list[str]
    project_questions: list[str]
    rag_agent_questions: list[str]
    behavioral_questions: list[str]
    suggested_answers_outline: list[str]
    analysis_mode: Literal["rules", "llm"] = "rules"
