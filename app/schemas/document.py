from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class DocumentUploadRequest(BaseModel):
    doc_type: str = "general"
    source: str | None = None


class DocumentSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    doc_type: str | None = None
    top_k: int | None = None
    score_threshold: float | None = None


class DocumentChunk(BaseModel):
    doc_id: str
    doc_type: str
    source: str
    chunk_id: int
    text: str
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentSearchResult(BaseModel):
    doc_id: str
    doc_type: str
    source: str
    chunk_id: int
    text: str
    score: float
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentUploadResponse(BaseModel):
    doc_id: str
    doc_type: str
    source: str
    chunk_count: int
