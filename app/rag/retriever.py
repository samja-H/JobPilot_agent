from __future__ import annotations

from app.core.config import Settings
from app.rag.embeddings import EmbeddingProvider
from app.rag.vector_store import QdrantVectorStore
from app.schemas.document import DocumentSearchRequest, DocumentSearchResult


class DocumentRetriever:
    def __init__(
        self,
        settings: Settings,
        embedding_provider: EmbeddingProvider,
        vector_store: QdrantVectorStore,
    ) -> None:
        self.settings: Settings = settings
        self.embedding_provider: EmbeddingProvider = embedding_provider
        self.vector_store: QdrantVectorStore = vector_store

    def search(self, request: DocumentSearchRequest) -> list[DocumentSearchResult]:
        top_k: int = request.top_k or self.settings.rag.top_k
        score_threshold: float | None = (
            request.score_threshold
            if request.score_threshold is not None
            else self.settings.rag.score_threshold
        )
        query_vector: list[float] = self.embedding_provider.embed_query(request.query)
        return self.vector_store.search(
            query_vector=query_vector,
            top_k=top_k,
            doc_type=request.doc_type,
            score_threshold=score_threshold,
        )
