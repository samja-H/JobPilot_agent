from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

AgentIntent = Literal[
    "rag_qa",
    "jd_analysis",
    "resume_match",
    "resume_rewrite",
    "interview_questions",
    "application_query",
    "general_chat",
]

ToolCallStatus = Literal["success", "blocked", "error", "skipped"]


class ToolCallRecord(BaseModel):
    tool_name: str
    status: ToolCallStatus
    input_summary: str
    output_summary: str


class AgentChatRequest(BaseModel):
    message: str = Field(min_length=1)
    resume_text: str | None = None
    jd_text: str | None = None
    project_experience: str | None = None
    rag_context: list[str] = Field(default_factory=list)
    doc_type: str | None = None
    company: str | None = None
    position: str | None = None
    status: str | None = None
    source: str | None = None
    limit: int = Field(default=5, ge=1, le=50)


class AgentChatResponse(BaseModel):
    intent: AgentIntent
    answer: str
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    data: dict[str, Any] = Field(default_factory=dict)
