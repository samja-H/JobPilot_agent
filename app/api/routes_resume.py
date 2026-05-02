from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import Settings, get_settings
from app.schemas.resume import ResumeMatchRequest, ResumeMatchResponse
from app.tools.resume_matcher import match_resume_to_jd_tool

router: APIRouter = APIRouter(prefix="/resume", tags=["resume"])


@router.post("/match", response_model=ResumeMatchResponse)
def match_resume(
    request: ResumeMatchRequest,
    settings: Annotated[Settings, Depends(get_settings)],
) -> ResumeMatchResponse:
    try:
        return match_resume_to_jd_tool(request=request, settings=settings)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
