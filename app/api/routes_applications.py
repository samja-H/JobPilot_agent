from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.config import Settings, get_settings
from app.db.repositories import ApplicationRepository
from app.schemas.application import (
    ApplicationCreateRequest,
    ApplicationResponse,
    ApplicationSearchRequest,
    ApplicationUpdateRequest,
)
from app.tools.application_tracker import (
    create_application_tool,
    search_applications_tool,
    update_application_status_tool,
)

router: APIRouter = APIRouter(prefix="/applications", tags=["applications"])


def get_application_repository(
    settings: Annotated[Settings, Depends(get_settings)],
) -> ApplicationRepository:
    return ApplicationRepository(settings=settings)


@router.post("", response_model=ApplicationResponse)
def create_application(
    request: ApplicationCreateRequest,
    repository: Annotated[ApplicationRepository, Depends(get_application_repository)],
) -> ApplicationResponse:
    try:
        return create_application_tool(request=request, repository=repository)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get("", response_model=list[ApplicationResponse])
def search_applications(
    repository: Annotated[ApplicationRepository, Depends(get_application_repository)],
    company: str | None = None,
    position: str | None = None,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    source: str | None = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ApplicationResponse]:
    request = ApplicationSearchRequest(
        company=company,
        position=position,
        status=status_filter,
        source=source,
        limit=limit,
        offset=offset,
    )
    return search_applications_tool(request=request, repository=repository)


@router.patch("/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: int,
    request: ApplicationUpdateRequest,
    repository: Annotated[ApplicationRepository, Depends(get_application_repository)],
) -> ApplicationResponse:
    try:
        return update_application_status_tool(
            application_id=application_id,
            request=request,
            repository=repository,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
