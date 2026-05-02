from __future__ import annotations

import hashlib
import math
from abc import ABC, abstractmethod

from app.core.config import Settings


class EmbeddingProvider(ABC):
    @property
    @abstractmethod
    def dimension(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def embed_query(self, text: str) -> list[float]:
        raise NotImplementedError

    @abstractmethod
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class MockEmbedding(EmbeddingProvider):
    def __init__(self, dimension: int = 384) -> None:
        if dimension <= 0:
            raise ValueError("embedding dimension must be greater than 0")
        self._dimension: int = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def _embed(self, text: str) -> list[float]:
        seed: bytes = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        counter: int = 0

        while len(values) < self._dimension:
            block: bytes = hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
            values.extend((byte / 127.5) - 1.0 for byte in block)
            counter += 1

        vector: list[float] = values[: self._dimension]
        norm: float = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]


class OpenAIEmbedding(EmbeddingProvider):
    def __init__(self, model: str, dimension: int, api_key: str | None) -> None:
        self.model: str = model
        self.api_key: str | None = api_key
        self._dimension: int = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_query(self, text: str) -> list[float]:
        raise NotImplementedError("OpenAI embedding provider is reserved for a later iteration")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("OpenAI embedding provider is reserved for a later iteration")


class DashScopeEmbedding(EmbeddingProvider):
    def __init__(self, model: str, dimension: int, api_key: str | None) -> None:
        self.model: str = model
        self.api_key: str | None = api_key
        self._dimension: int = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_query(self, text: str) -> list[float]:
        raise NotImplementedError("DashScope embedding provider is reserved for a later iteration")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("DashScope embedding provider is reserved for a later iteration")


def create_embedding_provider(settings: Settings) -> EmbeddingProvider:
    provider: str = settings.embedding.provider.lower()
    if provider == "mock":
        return MockEmbedding(dimension=settings.embedding.dimension)
    if provider == "openai":
        return OpenAIEmbedding(
            model=settings.embedding.model,
            dimension=settings.embedding.dimension,
            api_key=settings.secrets.openai_api_key,
        )
    if provider == "dashscope":
        return DashScopeEmbedding(
            model=settings.embedding.model,
            dimension=settings.embedding.dimension,
            api_key=settings.secrets.dashscope_api_key,
        )

    raise ValueError(f"Unsupported embedding provider: {settings.embedding.provider}")
