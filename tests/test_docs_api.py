from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes_docs import get_document_service
from app.core.config import AppConfig, LoggingConfig, Settings
from app.main import create_app
from app.schemas.document import DocumentSearchRequest, DocumentSearchResult


class FakeDocumentService:
    def __init__(self) -> None:
        self.last_request: DocumentSearchRequest | None = None

    def search(self, request: DocumentSearchRequest) -> list[DocumentSearchResult]:
        self.last_request = request
        return [
            DocumentSearchResult(
                doc_id="doc-1",
                doc_type=request.doc_type or "resume",
                source="resume.md",
                chunk_id=0,
                text="Python FastAPI backend experience",
                score=0.91,
                created_at=datetime(2026, 5, 2, 0, 0, 0),
                metadata={
                    "doc_id": "doc-1",
                    "doc_type": request.doc_type or "resume",
                    "source": "resume.md",
                    "chunk_id": 0,
                    "created_at": "2026-05-02T00:00:00",
                },
            )
        ]


def test_docs_search_route_calls_document_service() -> None:
    settings = Settings(
        app=AppConfig(name="Test JobPilot", env="test", debug=False),
        logging=LoggingConfig(level="CRITICAL", log_file=None),
    )
    app: FastAPI = create_app(settings)
    fake_service = FakeDocumentService()
    app.dependency_overrides[get_document_service] = lambda: fake_service
    client = TestClient(app)

    response = client.post(
        "/docs/search",
        json={
            "query": "backend role",
            "doc_type": "resume",
            "top_k": 3,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["doc_id"] == "doc-1"
    assert payload[0]["doc_type"] == "resume"
    assert payload[0]["metadata"]["chunk_id"] == 0
    assert fake_service.last_request is not None
    assert fake_service.last_request.query == "backend role"
    assert fake_service.last_request.top_k == 3
