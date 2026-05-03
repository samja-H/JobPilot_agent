from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import Settings, get_settings
from app.schemas.interview import InterviewQuestionRequest, InterviewQuestionResponse
from app.tools.interview_question_generator import generate_interview_questions_tool

router: APIRouter = APIRouter(prefix="/interview", tags=["interview"])


@router.post("/questions", response_model=InterviewQuestionResponse)
def generate_interview_questions(
    request: InterviewQuestionRequest,
    settings: Annotated[Settings, Depends(get_settings)],
) -> InterviewQuestionResponse:
    try:
        return generate_interview_questions_tool(request=request, settings=settings)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
