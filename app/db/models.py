from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from sqlite3 import Row
from typing import Any


@dataclass(frozen=True)
class ApplicationRecord:
    id: int
    company: str
    position: str
    jd_text: str
    resume_version: str
    status: str
    apply_date: date | None
    source: str
    notes: str
    match_score: float | None
    next_action: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_row(cls, row: Row) -> "ApplicationRecord":
        values: dict[str, Any] = dict(row)
        return cls(
            id=int(values["id"]),
            company=str(values["company"]),
            position=str(values["position"]),
            jd_text=str(values["jd_text"]),
            resume_version=str(values["resume_version"]),
            status=str(values["status"]),
            apply_date=_parse_date(values["apply_date"]),
            source=str(values["source"]),
            notes=str(values["notes"]),
            match_score=_parse_float(values["match_score"]),
            next_action=str(values["next_action"]),
            created_at=_parse_datetime(values["created_at"]),
            updated_at=_parse_datetime(values["updated_at"]),
        )


def _parse_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    return date.fromisoformat(str(value))


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def _parse_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    return float(value)
