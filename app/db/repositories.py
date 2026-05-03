from __future__ import annotations

from datetime import UTC, datetime
from sqlite3 import Row
from typing import Any

from pydantic import BaseModel

from app.core.config import Settings
from app.db.models import ApplicationRecord
from app.db.session import get_db_connection, initialize_database
from app.schemas.application import ApplicationCreateRequest, ApplicationSearchRequest, ApplicationUpdateRequest


class ApplicationRepository:
    def __init__(self, settings: Settings) -> None:
        self.settings: Settings = settings
        initialize_database(settings)

    def create(self, request: ApplicationCreateRequest) -> ApplicationRecord:
        now: str = _utc_now()
        with get_db_connection(self.settings) as connection:
            cursor = connection.execute(
                """
                INSERT INTO application_records (
                    company,
                    position,
                    jd_text,
                    resume_version,
                    status,
                    apply_date,
                    source,
                    notes,
                    match_score,
                    next_action,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request.company.strip(),
                    request.position.strip(),
                    request.jd_text,
                    request.resume_version,
                    request.status,
                    _date_to_text(request.apply_date),
                    request.source,
                    request.notes,
                    request.match_score,
                    request.next_action,
                    now,
                    now,
                ),
            )
            record_id: int = int(cursor.lastrowid)
            row: Row | None = connection.execute(
                "SELECT * FROM application_records WHERE id = ?",
                (record_id,),
            ).fetchone()
        if row is None:
            raise RuntimeError("Created application record could not be loaded")
        return ApplicationRecord.from_row(row)

    def search(self, request: ApplicationSearchRequest) -> list[ApplicationRecord]:
        conditions: list[str] = []
        parameters: list[Any] = []

        if request.company:
            conditions.append("company LIKE ?")
            parameters.append(f"%{request.company}%")
        if request.position:
            conditions.append("position LIKE ?")
            parameters.append(f"%{request.position}%")
        if request.status:
            conditions.append("status = ?")
            parameters.append(request.status)
        if request.source:
            conditions.append("source LIKE ?")
            parameters.append(f"%{request.source}%")

        where_clause: str = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        parameters.extend([request.limit, request.offset])
        query: str = (
            "SELECT * FROM application_records "
            f"{where_clause} "
            "ORDER BY created_at DESC, id DESC "
            "LIMIT ? OFFSET ?"
        )

        with get_db_connection(self.settings) as connection:
            rows: list[Row] = connection.execute(query, parameters).fetchall()
        return [ApplicationRecord.from_row(row) for row in rows]

    def update(self, application_id: int, request: ApplicationUpdateRequest) -> ApplicationRecord | None:
        updates: dict[str, Any] = _model_to_update_dict(request)
        if not updates:
            return self.get_by_id(application_id)

        updates["updated_at"] = _utc_now()
        assignments: str = ", ".join(f"{field} = ?" for field in updates)
        parameters: list[Any] = [_serialize_update_value(value) for value in updates.values()]
        parameters.append(application_id)

        with get_db_connection(self.settings) as connection:
            cursor = connection.execute(
                f"UPDATE application_records SET {assignments} WHERE id = ?",
                parameters,
            )
            if cursor.rowcount == 0:
                return None
            row: Row | None = connection.execute(
                "SELECT * FROM application_records WHERE id = ?",
                (application_id,),
            ).fetchone()

        if row is None:
            return None
        return ApplicationRecord.from_row(row)

    def get_by_id(self, application_id: int) -> ApplicationRecord | None:
        with get_db_connection(self.settings) as connection:
            row: Row | None = connection.execute(
                "SELECT * FROM application_records WHERE id = ?",
                (application_id,),
            ).fetchone()
        if row is None:
            return None
        return ApplicationRecord.from_row(row)


def _model_to_update_dict(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_none=True)  # type: ignore[attr-defined]
    return model.dict(exclude_none=True)


def _serialize_update_value(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _date_to_text(value: Any) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")
