from __future__ import annotations

from pathlib import Path


def test_prompt_templates_are_not_written_in_routes() -> None:
    resume_route = Path("app/api/routes_resume.py").read_text(encoding="utf-8")
    interview_route = Path("app/api/routes_interview.py").read_text(encoding="utf-8")
    prompt_file = Path("app/tools/prompts.py").read_text(encoding="utf-8")

    assert "你是求职简历优化助手" in prompt_file
    assert "你是面试准备助手" in prompt_file
    assert "你是求职简历优化助手" not in resume_route
    assert "你是面试准备助手" not in interview_route
    assert "PROMPT_TEMPLATE" not in resume_route
    assert "PROMPT_TEMPLATE" not in interview_route
