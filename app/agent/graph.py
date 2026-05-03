from __future__ import annotations

from typing import Protocol

from app.agent.nodes import intent_router, rag_retrieve, response_generate, tool_call
from app.agent.state import AgentState
from app.core.config import Settings
from app.schemas.agent import AgentChatRequest, AgentChatResponse


class AgentWorkflow(Protocol):
    def invoke(self, state: AgentState) -> AgentState:
        raise NotImplementedError


class SequentialAgentWorkflow:
    def invoke(self, state: AgentState) -> AgentState:
        current_state: AgentState = intent_router(state)
        current_state = rag_retrieve(current_state)
        current_state = tool_call(current_state)
        current_state = response_generate(current_state)
        return current_state


def build_agent_graph() -> AgentWorkflow:
    try:
        from langgraph.graph import END, StateGraph
    except ImportError:
        return SequentialAgentWorkflow()

    workflow = StateGraph(AgentState)
    workflow.add_node("intent_router", intent_router)
    workflow.add_node("rag_retrieve", rag_retrieve)
    workflow.add_node("tool_call", tool_call)
    workflow.add_node("response_generate", response_generate)
    workflow.set_entry_point("intent_router")
    workflow.add_edge("intent_router", "rag_retrieve")
    workflow.add_edge("rag_retrieve", "tool_call")
    workflow.add_edge("tool_call", "response_generate")
    workflow.add_edge("response_generate", END)
    return workflow.compile()


def run_agent_chat(
    request: AgentChatRequest,
    settings: Settings,
    workflow: AgentWorkflow | None = None,
) -> AgentChatResponse:
    selected_workflow: AgentWorkflow = workflow or build_agent_graph()
    initial_state: AgentState = {
        "request": request,
        "settings": settings,
        "tool_calls": [],
        "iterations": 0,
    }
    final_state: AgentState = selected_workflow.invoke(initial_state)
    response: AgentChatResponse | None = final_state.get("response")
    if response is None:
        raise RuntimeError("Agent workflow did not generate a response")
    return response
