import pytest

from docmind.domain import Chunk, Citation

VALID_HASH = "b" * 64


def create_chunk(**changes: object) -> Chunk:
    values: dict[str, object] = {
        "id": "chk_001",
        "document_id": "doc_001",
        "document_version_id": "ver_001",
        "ordinal": 0,
        "text": "RAG combines retrieval with generation.",
        "content_hash": VALID_HASH,
        "source_uri": "E:/knowledge/rag.pdf",
        "page_number": 12,
        "heading": "Introduction",
    }
    values.update(changes)
    return Chunk(**values)


def test_create_chunk() -> None:
    chunk = create_chunk()

    assert chunk.id == "chk_001"
    assert chunk.document_version_id == "ver_001"
    assert chunk.ordinal == 0
    assert chunk.page_number == 12
    assert chunk.heading == "Introduction"


def test_chunk_allows_missing_page_and_heading() -> None:
    chunk = create_chunk(
        page_number=None,
        heading=None,
    )

    assert chunk.page_number is None
    assert chunk.heading is None


@pytest.mark.parametrize("ordinal", [-1, -100])
def test_chunk_rejects_negative_ordinal(ordinal: int) -> None:
    with pytest.raises(ValueError, match="ordinal"):
        create_chunk(ordinal=ordinal)


def test_chunk_rejects_boolean_ordinal() -> None:
    with pytest.raises(TypeError, match="ordinal"):
        create_chunk(ordinal=True)


def test_chunk_rejects_blank_text() -> None:
    with pytest.raises(ValueError, match="text"):
        create_chunk(text="  ")


def test_chunk_rejects_invalid_content_hash() -> None:
    with pytest.raises(ValueError, match="content_hash"):
        create_chunk(content_hash="invalid")


@pytest.mark.parametrize("page_number", [0, -1])
def test_chunk_rejects_non_positive_page_number(
    page_number: int,
) -> None:
    with pytest.raises(ValueError, match="page_number"):
        create_chunk(page_number=page_number)


def test_chunk_rejects_blank_heading() -> None:
    with pytest.raises(ValueError, match="heading"):
        create_chunk(heading=" ")


def test_create_citation_from_chunk() -> None:
    chunk = create_chunk()

    citation = Citation.from_chunk(chunk)

    assert citation.chunk_id == chunk.id
    assert citation.document_id == chunk.document_id
    assert citation.document_version_id == chunk.document_version_id
    assert citation.source_uri == chunk.source_uri
    assert citation.quote == chunk.text
    assert citation.page_number == chunk.page_number
    assert citation.heading == chunk.heading


def test_create_citation_with_selected_quote() -> None:
    chunk = create_chunk()

    citation = Citation.from_chunk(
        chunk,
        quote="retrieval with generation",
    )

    assert citation.quote == "retrieval with generation"


def test_citation_rejects_blank_quote() -> None:
    chunk = create_chunk()

    with pytest.raises(ValueError, match="quote"):
        Citation.from_chunk(chunk, quote=" ")


def test_citation_rejects_invalid_page_number() -> None:
    with pytest.raises(ValueError, match="page_number"):
        Citation(
            chunk_id="chk_001",
            document_id="doc_001",
            document_version_id="ver_001",
            source_uri="E:/knowledge/rag.pdf",
            quote="Referenced content",
            page_number=0,
        )