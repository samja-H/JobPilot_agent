from __future__ import annotations

RESUME_REWRITE_PROMPT_TEMPLATE: str = """
你是求职简历优化助手。请基于用户简历、项目经历、目标岗位 JD 和 RAG 检索上下文，
输出结构化的项目描述优化建议，重点突出与目标岗位相关的技能、动作、结果和风险点。

要求：
1. 不编造未提供的项目事实。
2. 优先使用 JD 中真实出现的技能词。
3. 输出可直接写入简历的项目描述和 bullet points。

简历：
{resume_text}

项目经历：
{project_experience}

岗位 JD：
{jd_text}

RAG 上下文：
{rag_context}
""".strip()

INTERVIEW_QUESTIONS_PROMPT_TEMPLATE: str = """
你是面试准备助手。请基于用户简历、项目经历、目标岗位 JD 和 RAG 检索上下文，
生成结构化面试问题，覆盖技术、项目深挖、RAG/Agent 方向和行为面。

要求：
1. 问题要围绕候选人简历和 JD 的匹配点。
2. 不生成与材料无关的泛泛问题。
3. 给出回答提纲，帮助候选人准备可验证的项目证据。

简历：
{resume_text}

项目经历：
{project_experience}

岗位 JD：
{jd_text}

RAG 上下文：
{rag_context}
""".strip()


def render_resume_rewrite_prompt(
    resume_text: str,
    project_experience: str,
    jd_text: str,
    rag_context: list[str],
) -> str:
    return RESUME_REWRITE_PROMPT_TEMPLATE.format(
        resume_text=resume_text,
        project_experience=project_experience,
        jd_text=jd_text,
        rag_context="\n".join(rag_context),
    )


def render_interview_questions_prompt(
    resume_text: str,
    project_experience: str,
    jd_text: str,
    rag_context: list[str],
) -> str:
    return INTERVIEW_QUESTIONS_PROMPT_TEMPLATE.format(
        resume_text=resume_text,
        project_experience=project_experience,
        jd_text=jd_text,
        rag_context="\n".join(rag_context),
    )
