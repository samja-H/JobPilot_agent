from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.agent.graph import run_agent_chat
from app.core.config import Settings, get_settings
from app.schemas.agent import AgentChatRequest, AgentChatResponse

router: APIRouter = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/chat", response_model=AgentChatResponse)
def agent_chat(
    request: AgentChatRequest,
    settings: Annotated[Settings, Depends(get_settings)],
) -> AgentChatResponse:
    return run_agent_chat(request=request, settings=settings)
