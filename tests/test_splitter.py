from __future__ import annotations

import pytest

from app.rag.splitter import TextSplitter


def test_text_splitter_uses_overlap() -> None:
    splitter = TextSplitter(chunk_size=10, chunk_overlap=3)

    chunks = splitter.split_text("abcdefghijklmnopqrstuvwxyz")

    assert chunks == ["abcdefghij", "hijklmnopq", "opqrstuvwx", "vwxyz"]


def test_text_splitter_rejects_invalid_overlap() -> None:
    with pytest.raises(ValueError):
        TextSplitter(chunk_size=10, chunk_overlap=10)
