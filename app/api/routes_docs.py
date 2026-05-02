from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.core.config import Settings, get_settings
from app.rag.service import DocumentService, create_document_service
from app.schemas.document import (
    DocumentSearchRequest,
    DocumentSearchResult,
    DocumentUploadRequest,
    DocumentUploadResponse,
)

router: APIRouter = APIRouter(prefix="/docs", tags=["documents"])


def get_document_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> DocumentService:
    return create_document_service(settings)


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    service: Annotated[DocumentService, Depends(get_document_service)],
    file: UploadFile = File(...),
    doc_type: str = Form("general"),
    source: str | None = Form(None),
) -> DocumentUploadResponse:
    content: bytes = await file.read()
    request = DocumentUploadRequest(
        doc_type=doc_type,
        source=source or file.filename,
    )
    return service.upload_document(
        filename=file.filename or request.source or "uploaded.txt",
        content=content,
        request=request,
    )


@router.post("/search", response_model=list[DocumentSearchResult])
def search_documents(
    request: DocumentSearchRequest,
    service: Annotated[DocumentService, Depends(get_document_service)],
) -> list[DocumentSearchResult]:
    return service.search(request)
