from __future__ import annotations

from app.core.config import Settings


class TextSplitter:
    def __init__(self, chunk_size: int, chunk_overlap: int) -> None:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than 0")
        if chunk_overlap < 0:
            raise ValueError("chunk_overlap must be greater than or equal to 0")
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")

        self.chunk_size: int = chunk_size
        self.chunk_overlap: int = chunk_overlap

    @classmethod
    def from_settings(cls, settings: Settings) -> "TextSplitter":
        return cls(
            chunk_size=settings.rag.chunk_size,
            chunk_overlap=settings.rag.chunk_overlap,
        )

    def split_text(self, text: str) -> list[str]:
        normalized_text: str = text.strip()
        if not normalized_text:
            return []

        chunks: list[str] = []
        start: int = 0
        while start < len(normalized_text):
            end: int = min(start + self.chunk_size, len(normalized_text))
            chunk: str = normalized_text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end == len(normalized_text):
                break
            start = end - self.chunk_overlap

        return chunks
