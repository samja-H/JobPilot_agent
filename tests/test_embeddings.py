from __future__ import annotations

import math

from app.rag.embeddings import MockEmbedding


def test_mock_embedding_is_deterministic_and_sized() -> None:
    embedding = MockEmbedding(dimension=8)

    first = embedding.embed_query("python backend developer")
    second = embedding.embed_query("python backend developer")

    assert first == second
    assert len(first) == 8
    assert math.isclose(sum(value * value for value in first), 1.0)


def test_mock_embedding_embeds_documents() -> None:
    embedding = MockEmbedding(dimension=4)

    vectors = embedding.embed_documents(["resume", "job description"])

    assert len(vectors) == 2
    assert all(len(vector) == 4 for vector in vectors)
