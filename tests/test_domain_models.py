from datetime import datetime, timezone

import pytest

from docmind.domain import Document, DocumentVersion

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)
VALID_HASH = "a" * 64


def test_create_document() -> None:
    document = Document(
        id="doc_001",
        source_uri="E:/knowledge/notes.md",
        title="RAG Notes",
        media_type="text/markdown",
        created_at=NOW,
    )

    assert document.id == "doc_001"
    assert document.source_uri == "E:/knowledge/notes.md"
    assert document.title == "RAG Notes"
    assert document.media_type == "text/markdown"
    assert document.created_at == NOW


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("id", ""),
        ("source_uri", "  "),
        ("title", "\t"),
        ("media_type", "\n"),
    ],
)
def test_document_rejects_blank_strings(
    field_name: str,
    value: str,
) -> None:
    values = {
        "id": "doc_001",
        "source_uri": "E:/knowledge/notes.md",
        "title": "RAG Notes",
        "media_type": "text/markdown",
        "created_at": NOW,
    }
    values[field_name] = value

    with pytest.raises(ValueError, match=field_name):
        Document(**values)


def test_document_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError, match="时区"):
        Document(
            id="doc_001",
            source_uri="E:/knowledge/notes.md",
            title="RAG Notes",
            media_type="text/markdown",
            created_at=datetime(2026, 1, 1),
        )


def test_create_document_version() -> None:
    version = DocumentVersion(
        id="ver_001",
        document_id="doc_001",
        content_hash=VALID_HASH,
        size_bytes=1024,
        parser_version="markdown-v1",
        created_at=NOW,
    )

    assert version.id == "ver_001"
    assert version.document_id == "doc_001"
    assert version.content_hash == VALID_HASH
    assert version.size_bytes == 1024
    assert version.parser_version == "markdown-v1"
    assert version.created_at == NOW


@pytest.mark.parametrize(
    "content_hash",
    [
        "",
        "abc",
        "A" * 64,
        "g" * 64,
        "a" * 63,
        "a" * 65,
    ],
)
def test_document_version_rejects_invalid_sha256(
    content_hash: str,
) -> None:
    with pytest.raises(ValueError, match="content_hash"):
        DocumentVersion(
            id="ver_001",
            document_id="doc_001",
            content_hash=content_hash,
            size_bytes=1024,
            parser_version="markdown-v1",
            created_at=NOW,
        )


def test_document_version_allows_empty_file() -> None:
    version = DocumentVersion(
        id="ver_001",
        document_id="doc_001",
        content_hash=VALID_HASH,
        size_bytes=0,
        parser_version="markdown-v1",
        created_at=NOW,
    )

    assert version.size_bytes == 0


def test_document_version_rejects_negative_size() -> None:
    with pytest.raises(ValueError, match="size_bytes"):
        DocumentVersion(
            id="ver_001",
            document_id="doc_001",
            content_hash=VALID_HASH,
            size_bytes=-1,
            parser_version="markdown-v1",
            created_at=NOW,
        )


def test_document_version_rejects_boolean_size() -> None:
    with pytest.raises(TypeError, match="size_bytes"):
        DocumentVersion(
            id="ver_001",
            document_id="doc_001",
            content_hash=VALID_HASH,
            size_bytes=True,
            parser_version="markdown-v1",
            created_at=NOW,
        )


def test_document_version_rejects_blank_document_id() -> None:
    with pytest.raises(ValueError, match="document_id"):
        DocumentVersion(
            id="ver_001",
            document_id=" ",
            content_hash=VALID_HASH,
            size_bytes=1024,
            parser_version="markdown-v1",
            created_at=NOW,
        )