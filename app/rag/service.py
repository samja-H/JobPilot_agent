from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from app.core.config import Settings
from app.rag.embeddings import EmbeddingProvider, create_embedding_provider
from app.rag.loaders import load_document_text
from app.rag.retriever import DocumentRetriever
from app.rag.splitter import TextSplitter
from app.rag.vector_store import QdrantVectorStore
from app.schemas.document import (
    DocumentChunk,
    DocumentSearchRequest,
    DocumentSearchResult,
    DocumentUploadRequest,
    DocumentUploadResponse,
)


class DocumentService:
    def __init__(
        self,
        settings: Settings,
        splitter: TextSplitter,
        embedding_provider: EmbeddingProvider,
        vector_store: QdrantVectorStore,
    ) -> None:
        self.settings: Settings = settings
        self.splitter: TextSplitter = splitter
        self.embedding_provider: EmbeddingProvider = embedding_provider
        self.vector_store: QdrantVectorStore = vector_store
        self.retriever: DocumentRetriever = DocumentRetriever(
            settings=settings,
            embedding_provider=embedding_provider,
            vector_store=vector_store,
        )

    def upload_document(
        self,
        filename: str,
        content: bytes,
        request: DocumentUploadRequest,
    ) -> DocumentUploadResponse:
        text: str = load_document_text(filename=filename, content=content)
        split_texts: list[str] = self.splitter.split_text(text)
        if not split_texts:
            raise ValueError("Document text is empty after splitting")

        doc_id: str = str(uuid4())
        source: str = request.source or filename
        created_at: datetime = datetime.utcnow()
        chunks: list[DocumentChunk] = [
            DocumentChunk(
                doc_id=doc_id,
                doc_type=request.doc_type,
                source=source,
                chunk_id=index,
                text=chunk_text,
                created_at=created_at,
                metadata={
                    "doc_id": doc_id,
                    "doc_type": request.doc_type,
                    "source": source,
                    "chunk_id": index,
                    "created_at": created_at.isoformat(),
                },
            )
            for index, chunk_text in enumerate(split_texts)
        ]

        embeddings: list[list[float]] = self.embedding_provider.embed_documents(
            [chunk.text for chunk in chunks]
        )
        self.vector_store.ensure_collection(self.embedding_provider.dimension)
        self.vector_store.upsert_chunks(chunks=chunks, embeddings=embeddings)

        return DocumentUploadResponse(
            doc_id=doc_id,
            doc_type=request.doc_type,
            source=source,
            chunk_count=len(chunks),
        )

    def search(self, request: DocumentSearchRequest) -> list[DocumentSearchResult]:
        return self.retriever.search(request)


def create_document_service(settings: Settings) -> DocumentService:
    embedding_provider: EmbeddingProvider = create_embedding_provider(settings)
    return DocumentService(
        settings=settings,
        splitter=TextSplitter.from_settings(settings),
        embedding_provider=embedding_provider,
        vector_store=QdrantVectorStore(settings),
    )

