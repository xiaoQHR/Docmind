from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _require_non_blank(value: str, field_name: str) -> None:
    """校验字符串不为空，并且不全是空白字符。"""
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} 必须是 str，实际为 {type(value).__name__}"
        )
    if not value.strip():
        raise ValueError(f"{field_name} 不能为空或全为空格")


def _require_aware_datetime(value: datetime, field_name: str) -> None:
    """校验 datetime 包含有效时区。"""
    if not isinstance(value, datetime):
        raise TypeError(
            f"{field_name} 必须是 datetime，实际为 {type(value).__name__}"
        )
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} 必须包含时区信息")


def _require_sha256_hex(value: str, field_name: str) -> None:
    """校验字符串是 64 位小写十六进制 SHA-256。"""
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} 必须是 str，实际为 {type(value).__name__}"
        )
    if _SHA256_RE.fullmatch(value) is None:
        raise ValueError(
            f"{field_name} 必须是 64 位小写十六进制 SHA-256 字符串"
        )


def _require_non_negative_int(value: int, field_name: str) -> None:
    """校验整数大于或等于 0，同时排除 bool。"""
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(
            f"{field_name} 必须是 int，实际为 {type(value).__name__}"
        )
    if value < 0:
        raise ValueError(f"{field_name} 不能小于 0")



def _require_positive_int(value: int, field_name: str) -> None:
    """校验整数大于 0，同时排除 bool。"""
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(
            f"{field_name} 必须是 int，实际为 {type(value).__name__}"
        )
    if value <= 0:
        raise ValueError(f"{field_name} 必须大于 0")

@dataclass(frozen=True, slots=True)
class Document:
    """一份逻辑文档。

    同一路径的源文件即使内容发生变化，Document.id 仍保持不变。
    """

    id: str
    source_uri: str
    title: str
    media_type: str
    created_at: datetime

    def __post_init__(self) -> None:
        _require_non_blank(self.id, "id")
        _require_non_blank(self.source_uri, "source_uri")
        _require_non_blank(self.title, "title")
        _require_non_blank(self.media_type, "media_type")
        _require_aware_datetime(self.created_at, "created_at")


@dataclass(frozen=True, slots=True)
class DocumentVersion:
    """一份逻辑文档在某个时间点的不可变内容版本。"""

    id: str
    document_id: str
    content_hash: str
    size_bytes: int
    parser_version: str
    created_at: datetime

    def __post_init__(self) -> None:
        _require_non_blank(self.id, "id")
        _require_non_blank(self.document_id, "document_id")
        _require_sha256_hex(self.content_hash, "content_hash")
        _require_non_negative_int(self.size_bytes, "size_bytes")
        _require_non_blank(self.parser_version, "parser_version")
        _require_aware_datetime(self.created_at, "created_at")


@dataclass(frozen=True, slots=True)
class Chunk:
    """参与索引和检索的最小内容单元。

    Chunk 必须绑定到具体的 DocumentVersion，避免不同版本的内容混用。
    """

    id: str
    document_id: str
    document_version_id: str
    ordinal: int
    text: str
    content_hash: str
    source_uri: str
    page_number: int | None = None
    heading: str | None = None

    def __post_init__(self) -> None:
        _require_non_blank(self.id, "id")
        _require_non_blank(self.document_id, "document_id")
        _require_non_blank(
            self.document_version_id,
            "document_version_id",
        )
        _require_non_negative_int(self.ordinal, "ordinal")
        _require_non_blank(self.text, "text")
        _require_sha256_hex(self.content_hash, "content_hash")
        _require_non_blank(self.source_uri, "source_uri")

        if self.page_number is not None:
            _require_positive_int(self.page_number, "page_number")

        if self.heading is not None:
            _require_non_blank(self.heading, "heading")


@dataclass(frozen=True, slots=True)
class Citation:
    """回答中使用的一条可追溯引用。"""

    chunk_id: str
    document_id: str
    document_version_id: str
    source_uri: str
    quote: str
    page_number: int | None = None
    heading: str | None = None

    def __post_init__(self) -> None:
        _require_non_blank(self.chunk_id, "chunk_id")
        _require_non_blank(self.document_id, "document_id")
        _require_non_blank(
            self.document_version_id,
            "document_version_id",
        )
        _require_non_blank(self.source_uri, "source_uri")
        _require_non_blank(self.quote, "quote")

        if self.page_number is not None:
            _require_positive_int(self.page_number, "page_number")

        if self.heading is not None:
            _require_non_blank(self.heading, "heading")

    @classmethod
    def from_chunk(
        cls,
        chunk: Chunk,
        quote: str | None = None,
    ) -> Citation:
        """根据 Chunk 创建引用，默认引用完整 Chunk 文本。"""
        return cls(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            document_version_id=chunk.document_version_id,
            source_uri=chunk.source_uri,
            quote=chunk.text if quote is None else quote,
            page_number=chunk.page_number,
            heading=chunk.heading,
        )