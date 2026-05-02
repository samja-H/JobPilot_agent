from __future__ import annotations

from io import BytesIO
from pathlib import Path

SUPPORTED_EXTENSIONS: set[str] = {".pdf", ".docx", ".md", ".txt"}


def load_document_text(filename: str, content: bytes) -> str:
    extension: str = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        supported: str = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(f"Unsupported document type: {extension}. Supported: {supported}")

    if extension in {".md", ".txt"}:
        return _decode_text(content)
    if extension == ".pdf":
        return _load_pdf(content)
    if extension == ".docx":
        return _load_docx(content)

    raise ValueError(f"Unsupported document type: {extension}")


def _decode_text(content: bytes) -> str:
    text: str = content.decode("utf-8", errors="replace").strip()
    if not text:
        raise ValueError("Document text is empty")
    return text


def _load_pdf(content: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("PDF parsing requires the pypdf package") from exc

    reader = PdfReader(BytesIO(content))
    pages: list[str] = []
    for page in reader.pages:
        page_text: str | None = page.extract_text()
        if page_text:
            pages.append(page_text)

    text: str = "\n\n".join(pages).strip()
    if not text:
        raise ValueError("PDF document text is empty")
    return text


def _load_docx(content: bytes) -> str:
    try:
        from docx import Document
    except ImportError as exc:
        raise RuntimeError("DOCX parsing requires the python-docx package") from exc

    document = Document(BytesIO(content))
    paragraphs: list[str] = [
        paragraph.text.strip()
        for paragraph in document.paragraphs
        if paragraph.text.strip()
    ]

    text: str = "\n\n".join(paragraphs).strip()
    if not text:
        raise ValueError("DOCX document text is empty")
    return text
