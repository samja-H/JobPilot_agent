from __future__ import annotations

import json
import mimetypes
import sys
import uuid
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT_DIR: Path = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from app.core.config import get_settings  # noqa: E402

NAV_ITEMS: tuple[str, ...] = (
    "首页",
    "文档上传",
    "知识库检索",
    "JD 分析",
    "简历匹配",
    "简历优化",
    "面试问题",
    "投递记录",
    "Agent 对话",
)


def main() -> None:
    st = _load_streamlit()
    settings = get_settings()
    backend_url: str = _normalize_backend_url(settings.frontend.backend_url)

    st.set_page_config(page_title=settings.app.name, page_icon="JP", layout="wide")
    st.sidebar.title(settings.app.name)
    st.sidebar.caption(f"Frontend port: {settings.frontend.port}")
    st.sidebar.caption(f"Backend: {backend_url}")
    page: str = st.sidebar.radio("功能导航", NAV_ITEMS)

    if page == "首页":
        render_home(st, backend_url)
    elif page == "文档上传":
        render_document_upload(st, backend_url)
    elif page == "知识库检索":
        render_document_search(st, backend_url)
    elif page == "JD 分析":
        render_jd_analysis(st, backend_url)
    elif page == "简历匹配":
        render_resume_match(st, backend_url)
    elif page == "简历优化":
        render_resume_rewrite(st, backend_url)
    elif page == "面试问题":
        render_interview_questions(st, backend_url)
    elif page == "投递记录":
        render_applications(st, backend_url)
    elif page == "Agent 对话":
        render_agent_chat(st, backend_url)


def render_home(st: Any, backend_url: str) -> None:
    st.title("JobPilot-Agent 求职 Agent Demo")
    st.write(
        "这是一个基于 FastAPI、Streamlit、RAG、Tool Calling 和 LangGraph 的求职 Agent 演示页面。"
    )
    st.info("前端只负责收集输入并调用后端 API，所有业务逻辑均由后端模块处理。")

    st.subheader("功能导航")
    st.markdown(
        """
- 文档上传：上传 PDF、DOCX、MD、TXT 到知识库。
- 知识库检索：检索已入库的简历、JD 或项目上下文。
- JD 分析：提取岗位类别、职责、技能和风险点。
- 简历匹配：计算简历与 JD 的匹配分和缺口。
- 简历优化：生成面向目标岗位的项目描述优化建议。
- 面试问题：生成技术、项目、RAG/Agent 和行为面问题。
- 投递记录：创建、查询、更新求职投递信息。
- Agent 对话：让后端 Agent 根据输入选择工具。
"""
    )
    st.code(f"Backend URL: {backend_url}")


def render_document_upload(st: Any, backend_url: str) -> None:
    st.title("文档上传")
    with st.form("docs_upload_form"):
        uploaded_file = st.file_uploader("选择文件", type=["pdf", "docx", "md", "txt"])
        doc_type = st.selectbox("文档类型", ["resume", "job_description", "application_note", "interview_note", "general"])
        source = st.text_input("来源", placeholder="例如 resume_v1.pdf")
        submitted = st.form_submit_button("上传并入库")

    if submitted:
        if uploaded_file is None:
            st.warning("请先选择文件。")
            return
        result = api_upload(
            backend_url=backend_url,
            path="/docs/upload",
            file_field="file",
            filename=uploaded_file.name,
            file_bytes=uploaded_file.getvalue(),
            fields={
                "doc_type": doc_type,
                "source": source or uploaded_file.name,
            },
        )
        show_result(st, result)


def render_document_search(st: Any, backend_url: str) -> None:
    st.title("知识库检索")
    with st.form("docs_search_form"):
        query = st.text_area("检索问题", height=120)
        doc_type = st.text_input("文档类型过滤", placeholder="resume / job_description / general")
        top_k = st.number_input("Top K", min_value=1, max_value=20, value=5)
        submitted = st.form_submit_button("检索")

    if submitted:
        payload = {
            "query": query,
            "doc_type": doc_type or None,
            "top_k": int(top_k),
        }
        show_result(st, api_json(backend_url, "POST", "/docs/search", payload))


def render_jd_analysis(st: Any, backend_url: str) -> None:
    st.title("JD 分析")
    with st.form("jd_analysis_form"):
        jd_text = st.text_area("岗位 JD", height=260)
        submitted = st.form_submit_button("分析 JD")

    if submitted:
        show_result(st, api_json(backend_url, "POST", "/jobs/analyze", {"jd_text": jd_text}))


def render_resume_match(st: Any, backend_url: str) -> None:
    st.title("简历匹配")
    with st.form("resume_match_form"):
        resume_text = st.text_area("简历内容", height=220)
        jd_text = st.text_area("岗位 JD", height=220)
        submitted = st.form_submit_button("计算匹配分")

    if submitted:
        payload = {
            "resume_text": resume_text,
            "jd_text": jd_text,
        }
        show_result(st, api_json(backend_url, "POST", "/resume/match", payload))


def render_resume_rewrite(st: Any, backend_url: str) -> None:
    st.title("简历优化")
    with st.form("resume_rewrite_form"):
        resume_text = st.text_area("简历内容", height=180)
        project_experience = st.text_area("项目经历", height=180)
        jd_text = st.text_area("岗位 JD", height=180)
        rag_context_text = st.text_area("RAG 检索上下文", height=100, placeholder="每行一条上下文，可选")
        submitted = st.form_submit_button("生成优化建议")

    if submitted:
        payload = {
            "resume_text": resume_text,
            "project_experience": project_experience,
            "jd_text": jd_text,
            "rag_context": split_lines(rag_context_text),
        }
        show_result(st, api_json(backend_url, "POST", "/resume/rewrite", payload))


def render_interview_questions(st: Any, backend_url: str) -> None:
    st.title("面试问题生成")
    with st.form("interview_questions_form"):
        resume_text = st.text_area("简历内容", height=180)
        project_experience = st.text_area("项目经历", height=180)
        jd_text = st.text_area("岗位 JD", height=180)
        rag_context_text = st.text_area("RAG 检索上下文", height=100, placeholder="每行一条上下文，可选")
        submitted = st.form_submit_button("生成面试问题")

    if submitted:
        payload = {
            "resume_text": resume_text,
            "project_experience": project_experience,
            "jd_text": jd_text,
            "rag_context": split_lines(rag_context_text),
        }
        show_result(st, api_json(backend_url, "POST", "/interview/questions", payload))


def render_applications(st: Any, backend_url: str) -> None:
    st.title("投递记录管理")
    create_tab, search_tab, update_tab = st.tabs(["创建记录", "查询记录", "更新状态"])

    with create_tab:
        with st.form("application_create_form"):
            company = st.text_input("公司")
            position = st.text_input("岗位")
            status = st.selectbox("状态", ["planned", "applied", "interviewing", "offer", "rejected", "closed"])
            apply_date = st.text_input("投递日期", placeholder="YYYY-MM-DD，可选")
            source = st.text_input("来源", placeholder="官网 / Boss / LinkedIn")
            resume_version = st.text_input("简历版本", placeholder="v1")
            match_score = st.number_input("匹配分", min_value=0.0, max_value=100.0, value=0.0)
            next_action = st.text_input("下一步动作")
            jd_text = st.text_area("JD 文本", height=120)
            notes = st.text_area("备注", height=100)
            submitted = st.form_submit_button("创建")

        if submitted:
            payload = {
                "company": company,
                "position": position,
                "status": status,
                "apply_date": apply_date or None,
                "source": source,
                "resume_version": resume_version,
                "match_score": float(match_score) if match_score > 0 else None,
                "next_action": next_action,
                "jd_text": jd_text,
                "notes": notes,
            }
            show_result(st, api_json(backend_url, "POST", "/applications", payload))

    with search_tab:
        with st.form("application_search_form"):
            company = st.text_input("公司过滤")
            position = st.text_input("岗位过滤")
            status_filter = st.text_input("状态过滤", placeholder="planned / applied / interviewing")
            source = st.text_input("来源过滤")
            limit = st.number_input("返回数量", min_value=1, max_value=50, value=20)
            submitted = st.form_submit_button("查询")

        if submitted:
            query = {
                "company": company,
                "position": position,
                "status": status_filter,
                "source": source,
                "limit": int(limit),
            }
            show_result(st, api_json(backend_url, "GET", "/applications", query=query))

    with update_tab:
        with st.form("application_update_form"):
            application_id = st.number_input("记录 ID", min_value=1, value=1)
            status = st.selectbox("新状态", ["planned", "applied", "interviewing", "offer", "rejected", "closed"])
            next_action = st.text_input("下一步动作")
            notes = st.text_area("备注", height=100)
            submitted = st.form_submit_button("更新")

        if submitted:
            payload = {
                "status": status,
                "next_action": next_action or None,
                "notes": notes or None,
            }
            show_result(st, api_json(backend_url, "PATCH", f"/applications/{int(application_id)}", payload))


def render_agent_chat(st: Any, backend_url: str) -> None:
    st.title("Agent 对话")
    with st.form("agent_chat_form"):
        message = st.text_area("用户输入", height=120)
        resume_text = st.text_area("简历内容", height=120)
        jd_text = st.text_area("岗位 JD", height=120)
        project_experience = st.text_area("项目经历", height=120)
        rag_context_text = st.text_area("RAG 上下文", height=80, placeholder="每行一条上下文，可选")
        company = st.text_input("公司过滤", placeholder="投递查询时可选")
        position = st.text_input("岗位过滤", placeholder="投递查询时可选")
        status_filter = st.text_input("状态过滤", placeholder="投递查询时可选")
        submitted = st.form_submit_button("发送给 Agent")

    if submitted:
        payload = {
            "message": message,
            "resume_text": resume_text or None,
            "jd_text": jd_text or None,
            "project_experience": project_experience or None,
            "rag_context": split_lines(rag_context_text),
            "company": company or None,
            "position": position or None,
            "status": status_filter or None,
        }
        show_result(st, api_json(backend_url, "POST", "/agent/chat", payload))


def api_json(
    backend_url: str,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    query: dict[str, Any] | None = None,
) -> dict[str, Any]:
    url: str = build_url(backend_url, path, query=query)
    body: bytes | None = None
    headers: dict[str, str] = {"Accept": "application/json"}
    if method != "GET":
        body = json.dumps(payload or {}, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(url=url, data=body, headers=headers, method=method)
    return send_request(request)


def api_upload(
    backend_url: str,
    path: str,
    file_field: str,
    filename: str,
    file_bytes: bytes,
    fields: dict[str, str],
) -> dict[str, Any]:
    boundary: str = f"----jobpilot-{uuid.uuid4().hex}"
    body: bytes = encode_multipart_form(
        boundary=boundary,
        file_field=file_field,
        filename=filename,
        file_bytes=file_bytes,
        fields=fields,
    )
    request = Request(
        url=build_url(backend_url, path),
        data=body,
        headers={
            "Accept": "application/json",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    return send_request(request)


def send_request(request: Request) -> dict[str, Any]:
    try:
        with urlopen(request, timeout=30) as response:
            return {
                "ok": True,
                "status": response.status,
                "data": json.loads(response.read().decode("utf-8") or "null"),
            }
    except HTTPError as exc:
        detail: Any
        try:
            detail = json.loads(exc.read().decode("utf-8"))
        except ValueError:
            detail = exc.reason
        return {
            "ok": False,
            "status": exc.code,
            "error": detail,
        }
    except URLError as exc:
        return {
            "ok": False,
            "status": None,
            "error": f"无法连接后端：{exc.reason}",
        }


def encode_multipart_form(
    boundary: str,
    file_field: str,
    filename: str,
    file_bytes: bytes,
    fields: dict[str, str],
) -> bytes:
    lines: list[bytes] = []
    for key, value in fields.items():
        lines.extend(
            [
                f"--{boundary}".encode("utf-8"),
                f'Content-Disposition: form-data; name="{key}"'.encode("utf-8"),
                b"",
                value.encode("utf-8"),
            ]
        )

    content_type: str = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    lines.extend(
        [
            f"--{boundary}".encode("utf-8"),
            (
                f'Content-Disposition: form-data; name="{file_field}"; '
                f'filename="{filename}"'
            ).encode("utf-8"),
            f"Content-Type: {content_type}".encode("utf-8"),
            b"",
            file_bytes,
            f"--{boundary}--".encode("utf-8"),
            b"",
        ]
    )
    return b"\r\n".join(lines)


def show_result(st: Any, result: dict[str, Any]) -> None:
    if result.get("ok"):
        st.success(f"请求成功：HTTP {result.get('status')}")
        st.json(result.get("data"))
        return

    status: Any = result.get("status")
    st.error(f"请求失败：HTTP {status if status is not None else 'N/A'}")
    st.json(result.get("error"))


def build_url(
    backend_url: str,
    path: str,
    query: dict[str, Any] | None = None,
) -> str:
    url: str = f"{_normalize_backend_url(backend_url)}{path}"
    filtered_query: dict[str, Any] = {
        key: value
        for key, value in (query or {}).items()
        if value not in (None, "")
    }
    if filtered_query:
        url = f"{url}?{urlencode(filtered_query)}"
    return url


def split_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _normalize_backend_url(backend_url: str) -> str:
    return backend_url.rstrip("/")


def _load_streamlit() -> Any:
    import streamlit as st

    return st


if __name__ == "__main__":
    main()
