from __future__ import annotations

from typing import Any

from app.agent.state import AgentState
from app.core.config import Settings
from app.db.repositories import ApplicationRepository
from app.rag.embeddings import create_embedding_provider
from app.rag.retriever import DocumentRetriever
from app.rag.vector_store import QdrantVectorStore
from app.schemas.agent import AgentChatRequest, AgentChatResponse, AgentIntent, ToolCallRecord
from app.schemas.application import ApplicationSearchRequest
from app.schemas.document import DocumentSearchRequest, DocumentSearchResult
from app.schemas.interview import InterviewQuestionRequest
from app.schemas.job import JDAnalyzeRequest
from app.schemas.resume import ResumeMatchRequest, ResumeRewriteRequest
from app.tools.application_tracker import search_applications_tool
from app.tools.interview_question_generator import generate_interview_questions_tool
from app.tools.jd_analyzer import analyze_jd_tool
from app.tools.resume_matcher import match_resume_to_jd_tool
from app.tools.resume_rewriter import rewrite_resume_project_tool

TOOL_BY_INTENT: dict[AgentIntent, str] = {
    "rag_qa": "rag_retriever",
    "jd_analysis": "jd_analyzer",
    "resume_match": "resume_matcher",
    "resume_rewrite": "resume_rewriter",
    "interview_questions": "interview_question_generator",
    "application_query": "application_tracker",
}


def intent_router(state: AgentState) -> AgentState:
    request: AgentChatRequest = state["request"]
    message: str = request.message.lower()

    intent: AgentIntent
    if _has_any(message, ("面试", "interview", "追问")):
        intent = "interview_questions"
    elif _has_any(message, ("改写", "优化简历", "优化项目", "rewrite")):
        intent = "resume_rewrite"
    elif _has_any(message, ("匹配", "评分", "match")) and request.resume_text and request.jd_text:
        intent = "resume_match"
    elif _has_any(message, ("投递", "申请", "application", "进度", "状态")):
        intent = "application_query"
    elif _has_any(message, ("jd", "岗位", "职位", "招聘")) and _has_any(message, ("分析", "提取", "analyze")):
        intent = "jd_analysis"
    elif request.jd_text and not request.resume_text:
        intent = "jd_analysis"
    elif _has_any(message, ("检索", "知识库", "文档", "rag", "上下文")):
        intent = "rag_qa"
    else:
        intent = "general_chat"

    updated: AgentState = dict(state)
    updated["intent"] = intent
    updated.setdefault("tool_calls", [])
    updated.setdefault("iterations", 0)
    return updated


def rag_retrieve(state: AgentState) -> AgentState:
    if state.get("intent") != "rag_qa":
        return state

    updated: AgentState = dict(state)
    request: AgentChatRequest = state["request"]
    settings: Settings = state["settings"]
    allowed: bool = _is_tool_allowed(settings, "rag_retriever")
    if not allowed:
        _append_tool_call(
            updated,
            tool_name="rag_retriever",
            status="blocked",
            input_summary=_summarize_text(request.message),
            output_summary="Tool is not included in agent.allowed_tools.",
        )
        updated["rag_results"] = []
        return updated

    if request.rag_context:
        _append_tool_call(
            updated,
            tool_name="rag_retriever",
            status="success",
            input_summary=_summarize_text(request.message),
            output_summary=f"Loaded {len(request.rag_context)} context item(s) from request.",
        )
        updated["rag_results"] = [
            _context_to_search_result(index=index, text=text, doc_type=request.doc_type)
            for index, text in enumerate(request.rag_context)
        ]
        return updated

    try:
        embedding_provider = create_embedding_provider(settings)
        vector_store = QdrantVectorStore(settings)
        retriever = DocumentRetriever(
            settings=settings,
            embedding_provider=embedding_provider,
            vector_store=vector_store,
        )
        results: list[DocumentSearchResult] = retriever.search(
            DocumentSearchRequest(
                query=request.message,
                doc_type=request.doc_type,
                top_k=settings.rag.top_k,
            )
        )
        updated["rag_results"] = results
        _append_tool_call(
            updated,
            tool_name="rag_retriever",
            status="success",
            input_summary=_summarize_text(request.message),
            output_summary=f"Retrieved {len(results)} chunk(s).",
        )
    except Exception as exc:
        updated["rag_results"] = []
        _append_tool_call(
            updated,
            tool_name="rag_retriever",
            status="error",
            input_summary=_summarize_text(request.message),
            output_summary=str(exc),
        )
    return updated


def tool_call(state: AgentState) -> AgentState:
    intent: AgentIntent = state.get("intent", "general_chat")
    if intent in {"general_chat", "rag_qa"}:
        return state

    updated: AgentState = dict(state)
    settings: Settings = state["settings"]
    tool_name: str | None = TOOL_BY_INTENT.get(intent)
    if tool_name is None:
        return state

    if not settings.agent.enable_tool_calling:
        _append_tool_call(
            updated,
            tool_name=tool_name,
            status="blocked",
            input_summary=_summarize_text(state["request"].message),
            output_summary="Tool calling is disabled by agent.enable_tool_calling.",
        )
        return updated

    if updated.get("iterations", 0) >= settings.agent.max_iterations:
        _append_tool_call(
            updated,
            tool_name=tool_name,
            status="blocked",
            input_summary=_summarize_text(state["request"].message),
            output_summary="Agent max_iterations limit reached.",
        )
        return updated

    if not _is_tool_allowed(settings, tool_name):
        _append_tool_call(
            updated,
            tool_name=tool_name,
            status="blocked",
            input_summary=_summarize_text(state["request"].message),
            output_summary="Tool is not included in agent.allowed_tools.",
        )
        return updated

    try:
        output: Any = _execute_tool(intent=intent, state=updated)
        updated["tool_output"] = output
        updated["iterations"] = updated.get("iterations", 0) + 1
        _append_tool_call(
            updated,
            tool_name=tool_name,
            status="success",
            input_summary=_tool_input_summary(intent, state["request"]),
            output_summary=_output_summary(output),
        )
    except Exception as exc:
        updated["error"] = str(exc)
        _append_tool_call(
            updated,
            tool_name=tool_name,
            status="error",
            input_summary=_tool_input_summary(intent, state["request"]),
            output_summary=str(exc),
        )
    return updated


def response_generate(state: AgentState) -> AgentState:
    intent: AgentIntent = state.get("intent", "general_chat")
    tool_calls: list[ToolCallRecord] = state.get("tool_calls", [])
    output: Any = state.get("tool_output")
    rag_results: list[DocumentSearchResult] = state.get("rag_results", [])
    error: str | None = state.get("error")

    if error:
        answer: str = f"任务已识别为 {intent}，但工具调用失败：{error}"
        data: dict[str, Any] = {}
    elif intent == "rag_qa":
        answer, data = _rag_answer(rag_results=rag_results, request=state["request"])
    elif output is not None:
        answer = _tool_answer(intent=intent, output=output)
        data = _to_plain_data(output)
    else:
        answer = _general_answer(state["request"], tool_calls)
        data = {}

    updated: AgentState = dict(state)
    updated["response"] = AgentChatResponse(
        intent=intent,
        answer=answer,
        tool_calls=tool_calls,
        data=data,
    )
    return updated


def _execute_tool(intent: AgentIntent, state: AgentState) -> Any:
    request: AgentChatRequest = state["request"]
    settings: Settings = state["settings"]

    if intent == "jd_analysis":
        return analyze_jd_tool(
            request=JDAnalyzeRequest(jd_text=request.jd_text or request.message),
            settings=settings,
        )
    if intent == "resume_match":
        return match_resume_to_jd_tool(
            request=ResumeMatchRequest(
                resume_text=request.resume_text or "",
                jd_text=request.jd_text or "",
            ),
            settings=settings,
        )
    if intent == "resume_rewrite":
        return rewrite_resume_project_tool(
            request=ResumeRewriteRequest(
                resume_text=request.resume_text or request.message,
                project_experience=request.project_experience or request.resume_text or request.message,
                jd_text=request.jd_text or request.message,
                rag_context=request.rag_context,
            ),
            settings=settings,
        )
    if intent == "interview_questions":
        return generate_interview_questions_tool(
            request=InterviewQuestionRequest(
                resume_text=request.resume_text or request.message,
                project_experience=request.project_experience or request.resume_text or request.message,
                jd_text=request.jd_text or request.message,
                rag_context=request.rag_context,
            ),
            settings=settings,
        )
    if intent == "application_query":
        repository = ApplicationRepository(settings=settings)
        return search_applications_tool(
            request=ApplicationSearchRequest(
                company=request.company,
                position=request.position,
                status=request.status,
                source=request.source,
                limit=request.limit,
            ),
            repository=repository,
        )

    return None


def _rag_answer(
    rag_results: list[DocumentSearchResult],
    request: AgentChatRequest,
) -> tuple[str, dict[str, Any]]:
    if not rag_results:
        return (
            "我识别到这是 RAG 检索问答，但当前没有可用检索结果。请先上传文档或提供 rag_context。",
            {"results": []},
        )

    snippets: list[str] = [result.text for result in rag_results[:3]]
    answer: str = "基于检索上下文，建议优先参考以下信息：\n" + "\n".join(
        f"- {snippet}" for snippet in snippets
    )
    if request.message:
        answer += f"\n\n针对你的问题：{request.message}"
    return answer, {"results": [_to_plain_data(result) for result in rag_results]}


def _tool_answer(intent: AgentIntent, output: Any) -> str:
    if intent == "jd_analysis":
        return "已完成 JD 分析，结果包含岗位类别、职责、技能、关键词和风险点。"
    if intent == "resume_match":
        overall_score = getattr(output, "overall_score", None)
        return f"已完成简历匹配评分，综合分为 {overall_score}。"
    if intent == "resume_rewrite":
        return "已生成面向目标岗位的简历项目优化建议。"
    if intent == "interview_questions":
        return "已生成技术面、项目深挖、RAG/Agent 和行为面问题。"
    if intent == "application_query":
        count: int = len(output) if isinstance(output, list) else 0
        return f"已查询到 {count} 条投递记录。"
    return "已完成工具调用。"


def _general_answer(request: AgentChatRequest, tool_calls: list[ToolCallRecord]) -> str:
    if any(call.status == "blocked" for call in tool_calls):
        return "该任务需要调用工具，但当前工具不在白名单内或工具调用已关闭。"
    return (
        "我可以处理 JD 分析、简历匹配、简历优化、面试问题生成、投递记录查询和 RAG 检索。"
        "请补充对应的 jd_text、resume_text 或项目经历。"
    )


def _is_tool_allowed(settings: Settings, tool_name: str) -> bool:
    return tool_name in set(settings.agent.allowed_tools)


def _append_tool_call(
    state: AgentState,
    tool_name: str,
    status: str,
    input_summary: str,
    output_summary: str,
) -> None:
    state.setdefault("tool_calls", [])
    state["tool_calls"].append(
        ToolCallRecord(
            tool_name=tool_name,
            status=status,  # type: ignore[arg-type]
            input_summary=input_summary,
            output_summary=output_summary,
        )
    )


def _context_to_search_result(
    index: int,
    text: str,
    doc_type: str | None,
) -> DocumentSearchResult:
    from datetime import UTC, datetime

    return DocumentSearchResult(
        doc_id="request-context",
        doc_type=doc_type or "rag_context",
        source="request.rag_context",
        chunk_id=index,
        text=text,
        score=1.0,
        created_at=datetime.now(UTC),
        metadata={
            "doc_id": "request-context",
            "doc_type": doc_type or "rag_context",
            "source": "request.rag_context",
            "chunk_id": index,
        },
    )


def _tool_input_summary(intent: AgentIntent, request: AgentChatRequest) -> str:
    if intent == "resume_match":
        return f"resume={_len(request.resume_text)}, jd={_len(request.jd_text)}"
    if intent == "resume_rewrite":
        return f"project={_len(request.project_experience)}, jd={_len(request.jd_text)}"
    if intent == "interview_questions":
        return f"project={_len(request.project_experience)}, jd={_len(request.jd_text)}"
    if intent == "application_query":
        return f"company={request.company or '*'}, status={request.status or '*'}"
    return _summarize_text(request.jd_text or request.message)


def _output_summary(output: Any) -> str:
    if isinstance(output, list):
        return f"{len(output)} item(s)"
    data: dict[str, Any] = _to_plain_data(output)
    if "overall_score" in data:
        return f"overall_score={data['overall_score']}"
    if "job_category" in data:
        return f"job_category={data['job_category']}"
    return ", ".join(list(data.keys())[:5]) if data else "completed"


def _to_plain_data(value: Any) -> dict[str, Any]:
    if isinstance(value, list):
        return {"items": [_to_plain_data(item) for item in value]}
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")  # type: ignore[attr-defined]
    if hasattr(value, "dict"):
        return value.dict()
    if isinstance(value, dict):
        return value
    return {"value": value}


def _summarize_text(text: str | None, limit: int = 80) -> str:
    if not text:
        return ""
    normalized: str = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit].rstrip()}..."


def _len(text: str | None) -> int:
    return len(text or "")


def _has_any(text: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword.lower() in text for keyword in keywords)
