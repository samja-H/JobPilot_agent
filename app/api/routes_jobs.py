from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import Settings, get_settings
from app.schemas.job import JDAnalyzeRequest, JDAnalyzeResponse
from app.tools.jd_analyzer import analyze_jd_tool

router: APIRouter = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/analyze", response_model=JDAnalyzeResponse)
def analyze_job(
    request: JDAnalyzeRequest,
    settings: Annotated[Settings, Depends(get_settings)],
) -> JDAnalyzeResponse:
    try:
        return analyze_jd_tool(request=request, settings=settings)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
