from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from app.core.config import Settings
from app.schemas.document import DocumentChunk, DocumentSearchResult


class QdrantVectorStore:
    def __init__(self, settings: Settings) -> None:
        try:
            from qdrant_client import QdrantClient
        except ImportError as exc:
            raise RuntimeError("QdrantVectorStore requires the qdrant-client package") from exc

        self.collection_name: str = settings.qdrant.collection_name
        self._client = QdrantClient(
            host=settings.qdrant.host,
            port=settings.qdrant.port,
            timeout=settings.qdrant.timeout,
        )

    def ensure_collection(self, dimension: int) -> None:
        try:
            self._client.get_collection(collection_name=self.collection_name)
            return
        except Exception:
            pass

        from qdrant_client.http import models

        self._client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=dimension,
                distance=models.Distance.COSINE,
            ),
        )

    def upsert_chunks(
        self,
        chunks: list[DocumentChunk],
        embeddings: list[list[float]],
    ) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length")

        from qdrant_client.http import models

        points: list[Any] = []
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            points.append(
                models.PointStruct(
                    id=str(uuid4()),
                    vector=embedding,
                    payload=_chunk_payload(chunk),
                )
            )

        if points:
            self._client.upsert(
                collection_name=self.collection_name,
                points=points,
            )

    def search(
        self,
        query_vector: list[float],
        top_k: int,
        doc_type: str | None = None,
        score_threshold: float | None = None,
    ) -> list[DocumentSearchResult]:
        query_filter: Any | None = None
        if doc_type:
            from qdrant_client.http import models

            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="doc_type",
                        match=models.MatchValue(value=doc_type),
                    )
                ]
            )

        search_kwargs: dict[str, Any] = {
            "collection_name": self.collection_name,
            "query_vector": query_vector,
            "query_filter": query_filter,
            "limit": top_k,
        }
        if score_threshold is not None:
            search_kwargs["score_threshold"] = score_threshold

        hits = self._client.search(**search_kwargs)

        return [_search_hit_to_result(hit) for hit in hits]


def _chunk_payload(chunk: DocumentChunk) -> dict[str, Any]:
    created_at: str = chunk.created_at.isoformat()
    metadata: dict[str, Any] = {
        **chunk.metadata,
        "doc_id": chunk.doc_id,
        "doc_type": chunk.doc_type,
        "source": chunk.source,
        "chunk_id": chunk.chunk_id,
        "created_at": created_at,
    }
    return {
        "doc_id": chunk.doc_id,
        "doc_type": chunk.doc_type,
        "source": chunk.source,
        "chunk_id": chunk.chunk_id,
        "text": chunk.text,
        "created_at": created_at,
        "metadata": metadata,
    }


def _search_hit_to_result(hit: Any) -> DocumentSearchResult:
    payload: dict[str, Any] = hit.payload or {}
    created_at_value: Any = payload.get("created_at")
    created_at: datetime
    if isinstance(created_at_value, datetime):
        created_at = created_at_value
    elif isinstance(created_at_value, str):
        created_at = datetime.fromisoformat(created_at_value)
    else:
        created_at = datetime.utcnow()

    return DocumentSearchResult(
        doc_id=str(payload.get("doc_id", "")),
        doc_type=str(payload.get("doc_type", "")),
        source=str(payload.get("source", "")),
        chunk_id=int(payload.get("chunk_id", 0)),
        text=str(payload.get("text", "")),
        score=float(hit.score),
        created_at=created_at,
        metadata=dict(payload.get("metadata") or {}),
    )
