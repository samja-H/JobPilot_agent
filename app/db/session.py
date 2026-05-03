from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.core.config import BASE_DIR, Settings


def resolve_sqlite_path(settings: Settings) -> Path:
    if settings.database.type.lower() != "sqlite":
        raise ValueError(f"Unsupported database type: {settings.database.type}")

    sqlite_path: Path = Path(settings.database.sqlite_path)
    if sqlite_path.is_absolute():
        return sqlite_path
    return BASE_DIR / sqlite_path


@contextmanager
def get_db_connection(settings: Settings) -> Iterator[sqlite3.Connection]:
    db_path: Path = resolve_sqlite_path(settings)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection: sqlite3.Connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database(settings: Settings) -> None:
    with get_db_connection(settings) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS application_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                position TEXT NOT NULL,
                jd_text TEXT NOT NULL DEFAULT '',
                resume_version TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL,
                apply_date TEXT,
                source TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                match_score REAL,
                next_action TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_application_records_status
            ON application_records(status)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_application_records_company
            ON application_records(company)
            """
        )
