from __future__ import annotations

from app.db.models import ApplicationRecord
from app.db.repositories import ApplicationRepository
from app.schemas.application import (
    ApplicationCreateRequest,
    ApplicationResponse,
    ApplicationSearchRequest,
    ApplicationUpdateRequest,
)


def create_application_tool(
    request: ApplicationCreateRequest,
    repository: ApplicationRepository,
) -> ApplicationResponse:
    record: ApplicationRecord = repository.create(request)
    return _record_to_response(record)


def search_applications_tool(
    request: ApplicationSearchRequest,
    repository: ApplicationRepository,
) -> list[ApplicationResponse]:
    records: list[ApplicationRecord] = repository.search(request)
    return [_record_to_response(record) for record in records]


def update_application_status_tool(
    application_id: int,
    request: ApplicationUpdateRequest,
    repository: ApplicationRepository,
) -> ApplicationResponse:
    record: ApplicationRecord | None = repository.update(
        application_id=application_id,
        request=request,
    )
    if record is None:
        raise LookupError(f"Application record not found: {application_id}")
    return _record_to_response(record)


def _record_to_response(record: ApplicationRecord) -> ApplicationResponse:
    return ApplicationResponse(
        id=record.id,
        company=record.company,
        position=record.position,
        jd_text=record.jd_text,
        resume_version=record.resume_version,
        status=record.status,
        apply_date=record.apply_date,
        source=record.source,
        notes=record.notes,
        match_score=record.match_score,
        next_action=record.next_action,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )
