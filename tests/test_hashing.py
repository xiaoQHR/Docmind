import hashlib
from pathlib import Path

import pytest

from docmind.hashing import (
    file_sha256,
    normalize_text,
    sha256_bytes,
    stable_id,
    text_sha256,
)


def test_sha256_bytes_matches_hashlib() -> None:
    expected = hashlib.sha256(b"abc").hexdigest()

    assert sha256_bytes(b"abc") == expected


def test_sha256_bytes_rejects_string() -> None:
    with pytest.raises(TypeError, match="data"):
        sha256_bytes("abc")


def test_file_sha256_reads_file_in_blocks(
    tmp_path: Path,
) -> None:
    path = tmp_path / "document.bin"
    content = b"abcdefghij"
    path.write_bytes(content)

    result = file_sha256(path, block_size=3)

    assert result == hashlib.sha256(content).hexdigest()


def test_file_sha256_supports_empty_file(
    tmp_path: Path,
) -> None:
    path = tmp_path / "empty.txt"
    path.write_bytes(b"")

    assert file_sha256(path) == hashlib.sha256(b"").hexdigest()


def test_file_sha256_rejects_missing_file(
    tmp_path: Path,
) -> None:
    path = tmp_path / "missing.txt"

    with pytest.raises(FileNotFoundError):
        file_sha256(path)


def test_file_sha256_rejects_directory(
    tmp_path: Path,
) -> None:
    with pytest.raises(IsADirectoryError):
        file_sha256(tmp_path)


@pytest.mark.parametrize("block_size", [0, -1])
def test_file_sha256_rejects_non_positive_block_size(
    tmp_path: Path,
    block_size: int,
) -> None:
    path = tmp_path / "document.txt"
    path.write_text("content", encoding="utf-8")

    with pytest.raises(ValueError, match="block_size"):
        file_sha256(path, block_size=block_size)


def test_file_sha256_rejects_boolean_block_size(
    tmp_path: Path,
) -> None:
    path = tmp_path / "document.txt"
    path.write_text("content", encoding="utf-8")

    with pytest.raises(TypeError, match="block_size"):
        file_sha256(path, block_size=True)


def test_normalize_text_normalizes_line_endings_and_spaces() -> None:
    source = "\ufeff\nFirst line   \r\nSecond line\t\r\n\n"

    assert normalize_text(source) == "First line\nSecond line"


def test_normalize_text_uses_unicode_nfc() -> None:
    decomposed = "Cafe\u0301"
    composed = "Café"

    assert normalize_text(decomposed) == composed


def test_text_sha256_ignores_supported_formatting_differences() -> None:
    first = "\ufeffTitle  \r\nContent\r\n"
    second = "Title\nContent"

    assert text_sha256(first) == text_sha256(second)


def test_text_sha256_preserves_meaningful_inner_spaces() -> None:
    assert text_sha256("hello world") != text_sha256("hello  world")


def test_stable_id_is_deterministic() -> None:
    first = stable_id("doc", "E:/knowledge/rag.pdf")
    second = stable_id("doc", "E:/knowledge/rag.pdf")

    assert first == second
    assert first.startswith("doc_")
    assert len(first) == len("doc_") + 24


def test_stable_id_separates_namespaces() -> None:
    value = "E:/knowledge/rag.pdf"

    assert stable_id("doc", value) != stable_id("ver", value)


def test_stable_id_uses_unambiguous_part_encoding() -> None:
    assert stable_id("chk", "ab", "c") != stable_id(
        "chk",
        "a",
        "bc",
    )


@pytest.mark.parametrize(
    "namespace",
    [
        "",
        "Doc",
        "1doc",
        "doc-version",
        "doc version",
    ],
)
def test_stable_id_rejects_invalid_namespace(
    namespace: str,
) -> None:
    with pytest.raises(ValueError, match="namespace"):
        stable_id(namespace, "value")


def test_stable_id_requires_at_least_one_part() -> None:
    with pytest.raises(ValueError, match="至少"):
        stable_id("doc")


@pytest.mark.parametrize("digest_length", [0, 8, 15, 65])
def test_stable_id_rejects_invalid_digest_length(
    digest_length: int,
) -> None:
    with pytest.raises(ValueError, match="digest_length"):
        stable_id(
            "doc",
            "value",
            digest_length=digest_length,
        )


def test_stable_id_rejects_empty_part() -> None:
    with pytest.raises(ValueError, match=r"parts\[0\]"):
        stable_id("doc", "")