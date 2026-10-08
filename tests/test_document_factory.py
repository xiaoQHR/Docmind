import hashlib
from datetime import datetime, timezone
from pathlib import Path

import pytest

from docmind.ingestion import (
    DocumentFactory,
    DocumentSnapshot,
    UnsupportedDocumentTypeError,
)

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def create_factory() -> DocumentFactory:
    return DocumentFactory(clock=lambda: NOW)


def test_create_document_snapshot_from_markdown(
    tmp_path: Path,
) -> None:
    path = tmp_path / "rag-notes.md"
    content = "# RAG\n\nRetrieval augmented generation."
    path.write_text(content, encoding="utf-8")

    snapshot = create_factory().create(
        path,
        parser_version="markdown-v1",
    )

    assert isinstance(snapshot, DocumentSnapshot)
    assert snapshot.document.id.startswith("doc_")
    assert snapshot.document.source_uri == path.resolve().as_uri()
    assert snapshot.document.title == "rag-notes"
    assert snapshot.document.media_type == "text/markdown"
    assert snapshot.document.created_at == NOW

    assert snapshot.version.id.startswith("ver_")
    assert snapshot.version.document_id == snapshot.document.id
    assert snapshot.version.content_hash == hashlib.sha256(
        path.read_bytes()
    ).hexdigest()
    assert snapshot.version.size_bytes == len(path.read_bytes())
    assert snapshot.version.parser_version == "markdown-v1"
    assert snapshot.version.created_at == NOW


def test_document_id_is_stable_for_same_source(
    tmp_path: Path,
) -> None:
    path = tmp_path / "notes.md"
    path.write_text("First version", encoding="utf-8")
    factory = create_factory()

    first = factory.create(
        path,
        parser_version="markdown-v1",
    )
    second = factory.create(
        path,
        parser_version="markdown-v1",
    )

    assert first.document.id == second.document.id
    assert first.version.id == second.version.id


def test_content_change_creates_new_version_id(
    tmp_path: Path,
) -> None:
    path = tmp_path / "notes.md"
    factory = create_factory()

    path.write_text("First version", encoding="utf-8")
    first = factory.create(
        path,
        parser_version="markdown-v1",
    )

    path.write_text("Second version", encoding="utf-8")
    second = factory.create(
        path,
        parser_version="markdown-v1",
    )

    assert first.document.id == second.document.id
    assert first.version.id != second.version.id
    assert (
        first.version.content_hash
        != second.version.content_hash
    )


def test_parser_change_creates_new_version_id(
    tmp_path: Path,
) -> None:
    path = tmp_path / "notes.md"
    path.write_text("Same content", encoding="utf-8")
    factory = create_factory()

    first = factory.create(
        path,
        parser_version="markdown-v1",
    )
    second = factory.create(
        path,
        parser_version="markdown-v2",
    )

    assert first.document.id == second.document.id
    assert first.version.content_hash == second.version.content_hash
    assert first.version.id != second.version.id


def test_custom_title_overrides_file_stem(
    tmp_path: Path,
) -> None:
    path = tmp_path / "notes.md"
    path.write_text("Content", encoding="utf-8")

    snapshot = create_factory().create(
        path,
        parser_version="markdown-v1",
        title="Personal RAG Notes",
    )

    assert snapshot.document.title == "Personal RAG Notes"


@pytest.mark.parametrize(
    ("suffix", "expected_media_type"),
    [
        (".pdf", "application/pdf"),
        (".md", "text/markdown"),
        (".markdown", "text/markdown"),
        (".mdx", "text/markdown"),
        (".txt", "text/plain"),
        (".png", "image/png"),
        (".jpg", "image/jpeg"),
        (".jpeg", "image/jpeg"),
        (".webp", "image/webp"),
        (".tif", "image/tiff"),
        (".tiff", "image/tiff"),
    ],
)
def test_supported_media_types(
    tmp_path: Path,
    suffix: str,
    expected_media_type: str,
) -> None:
    path = tmp_path / f"document{suffix}"
    path.write_bytes(b"content")

    snapshot = create_factory().create(
        path,
        parser_version="test-parser-v1",
    )

    assert snapshot.document.media_type == expected_media_type


def test_rejects_unsupported_document_type(
    tmp_path: Path,
) -> None:
    path = tmp_path / "document.docx"
    path.write_bytes(b"content")

    with pytest.raises(
        UnsupportedDocumentTypeError,
        match=r"\.docx",
    ):
        create_factory().create(
            path,
            parser_version="docx-v1",
        )


def test_rejects_file_without_extension(
    tmp_path: Path,
) -> None:
    path = tmp_path / "document"
    path.write_bytes(b"content")

    with pytest.raises(
        UnsupportedDocumentTypeError,
        match="无扩展名",
    ):
        create_factory().create(
            path,
            parser_version="unknown-v1",
        )


def test_rejects_missing_source(
    tmp_path: Path,
) -> None:
    path = tmp_path / "missing.md"

    with pytest.raises(FileNotFoundError):
        create_factory().create(
            path,
            parser_version="markdown-v1",
        )


def test_rejects_directory_source(
    tmp_path: Path,
) -> None:
    with pytest.raises(IsADirectoryError):
        create_factory().create(
            tmp_path,
            parser_version="markdown-v1",
        )


def test_rejects_blank_parser_version(
    tmp_path: Path,
) -> None:
    path = tmp_path / "notes.md"
    path.write_text("Content", encoding="utf-8")

    with pytest.raises(ValueError, match="parser_version"):
        create_factory().create(
            path,
            parser_version=" ",
        )


def test_rejects_blank_custom_title(
    tmp_path: Path,
) -> None:
    path = tmp_path / "notes.md"
    path.write_text("Content", encoding="utf-8")

    with pytest.raises(ValueError, match="title"):
        create_factory().create(
            path,
            parser_version="markdown-v1",
            title=" ",
        )