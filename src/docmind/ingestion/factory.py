from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from docmind.domain import Document, DocumentVersion
from docmind.hashing import file_sha256, stable_id

Clock = Callable[[], datetime]

SUPPORTED_MEDIA_TYPES: dict[str, str] = {
    ".pdf": "application/pdf",
    ".md": "text/markdown",
    ".markdown": "text/markdown",
    ".mdx": "text/markdown",
    ".txt": "text/plain",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
}


class UnsupportedDocumentTypeError(ValueError):
    """文件类型不在当前 DocMind 支持范围内。"""


class SourceChangedDuringReadError(RuntimeError):
    """计算文件指纹期间，源文件发生了变化。"""


@dataclass(frozen=True, slots=True)
class DocumentSnapshot:
    """一次文件登记产生的逻辑文档及其内容版本。"""

    document: Document
    version: DocumentVersion


def utc_now() -> datetime:
    """返回带 UTC 时区的当前时间。"""
    return datetime.now(timezone.utc)


class DocumentFactory:
    """根据本地文件创建 Document 和 DocumentVersion。"""

    def __init__(self, clock: Clock | None = None) -> None:
        self._clock = clock or utc_now

    def create(
        self,
        source: str | Path,
        *,
        parser_version: str,
        title: str | None = None,
    ) -> DocumentSnapshot:
        source_path = Path(source).expanduser()

        if not source_path.exists():
            raise FileNotFoundError(source_path)

        resolved_path = source_path.resolve()

        if not resolved_path.is_file():
            raise IsADirectoryError(resolved_path)

        media_type = self._detect_media_type(resolved_path)
        source_uri = resolved_path.as_uri()

        before_stat = resolved_path.stat()
        content_hash = file_sha256(resolved_path)
        after_stat = resolved_path.stat()

        if (
            before_stat.st_size != after_stat.st_size
            or before_stat.st_mtime_ns != after_stat.st_mtime_ns
        ):
            raise SourceChangedDuringReadError(
                f"计算文件指纹时源文件发生变化: {resolved_path}"
            )

        created_at = self._clock()
        document_id = stable_id("doc", source_uri)
        version_id = stable_id(
            "ver",
            document_id,
            content_hash,
            parser_version,
        )

        document = Document(
            id=document_id,
            source_uri=source_uri,
            title=resolved_path.stem if title is None else title,
            media_type=media_type,
            created_at=created_at,
        )

        version = DocumentVersion(
            id=version_id,
            document_id=document_id,
            content_hash=content_hash,
            size_bytes=after_stat.st_size,
            parser_version=parser_version,
            created_at=created_at,
        )

        return DocumentSnapshot(
            document=document,
            version=version,
        )

    @staticmethod
    def _detect_media_type(path: Path) -> str:
        suffix = path.suffix.lower()

        try:
            return SUPPORTED_MEDIA_TYPES[suffix]
        except KeyError as exc:
            raise UnsupportedDocumentTypeError(
                f"不支持的文档类型: {suffix or '<无扩展名>'}"
            ) from exc