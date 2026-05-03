from __future__ import annotations

from pathlib import Path

from app.core.config import DatabaseConfig, Settings, load_settings
from app.db.repositories import ApplicationRepository
from app.db.session import resolve_sqlite_path
from app.schemas.application import (
    ApplicationCreateRequest,
    ApplicationSearchRequest,
    ApplicationUpdateRequest,
)
from app.tools.application_tracker import (
    create_application_tool,
    search_applications_tool,
    update_application_status_tool,
)


def test_create_application_record(tmp_path: Path) -> None:
    repository = _repository(tmp_path)

    response = create_application_tool(
        request=ApplicationCreateRequest(
            company="OpenAI",
            position="Backend Engineer",
            jd_text="Python FastAPI",
            resume_version="v1",
            status="applied",
            source="LinkedIn",
            notes="Initial application",
            match_score=86.5,
            next_action="Prepare interview",
        ),
        repository=repository,
    )

    assert response.id > 0
    assert response.company == "OpenAI"
    assert response.position == "Backend Engineer"
    assert response.status == "applied"
    assert response.match_score == 86.5
    assert response.created_at <= response.updated_at


def test_search_application_records(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    create_application_tool(
        request=ApplicationCreateRequest(
            company="Alpha",
            position="Python Engineer",
            status="applied",
        ),
        repository=repository,
    )
    create_application_tool(
        request=ApplicationCreateRequest(
            company="Beta",
            position="Data Engineer",
            status="interviewing",
        ),
        repository=repository,
    )

    results = search_applications_tool(
        request=ApplicationSearchRequest(status="interviewing"),
        repository=repository,
    )

    assert len(results) == 1
    assert results[0].company == "Beta"
    assert results[0].status == "interviewing"


def test_update_application_status(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    created = create_application_tool(
        request=ApplicationCreateRequest(
            company="Gamma",
            position="RAG Engineer",
            status="planned",
        ),
        repository=repository,
    )

    updated = update_application_status_tool(
        application_id=created.id,
        request=ApplicationUpdateRequest(
            status="interviewing",
            next_action="Prepare RAG project deep dive",
        ),
        repository=repository,
    )

    assert updated.id == created.id
    assert updated.status == "interviewing"
    assert updated.next_action == "Prepare RAG project deep dive"
    assert updated.updated_at >= created.updated_at


def test_database_path_is_read_from_app_yaml(tmp_path: Path) -> None:
    db_path: Path = tmp_path / "from-yaml.db"
    config_path: Path = tmp_path / "app.yaml"
    config_path.write_text(
        f"""
database:
  type: sqlite
  sqlite_path: {db_path}
""".strip(),
        encoding="utf-8",
    )

    settings = load_settings(
        config_path=config_path,
        env_file=tmp_path / "missing.env",
        environ={},
    )
    repository = ApplicationRepository(settings=settings)

    create_application_tool(
        request=ApplicationCreateRequest(
            company="Config Corp",
            position="Config Engineer",
            status="planned",
        ),
        repository=repository,
    )

    assert resolve_sqlite_path(settings) == db_path
    assert db_path.exists()


def _repository(tmp_path: Path) -> ApplicationRepository:
    settings = Settings(
        database=DatabaseConfig(
            type="sqlite",
            sqlite_path=str(tmp_path / "applications.db"),
        )
    )
    return ApplicationRepository(settings=settings)
