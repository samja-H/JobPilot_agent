from __future__ import annotations

from typing import Any, TypedDict

from app.core.config import Settings
from app.schemas.agent import AgentChatRequest, AgentChatResponse, AgentIntent, ToolCallRecord
from app.schemas.document import DocumentSearchResult


class AgentState(TypedDict, total=False):
    request: AgentChatRequest
    settings: Settings
    intent: AgentIntent
    rag_results: list[DocumentSearchResult]
    tool_calls: list[ToolCallRecord]
    tool_output: Any
    response: AgentChatResponse
    error: str
    iterations: int
