from __future__ import annotations

import hashlib
import re
import unicodedata
from pathlib import Path

DEFAULT_BLOCK_SIZE = 1024 * 1024
DEFAULT_ID_DIGEST_LENGTH = 24

_NAMESPACE_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def sha256_bytes(data: bytes) -> str:
    """计算字节内容的 SHA-256。"""
    if not isinstance(data, bytes):
        raise TypeError(
            f"data 必须是 bytes，实际为 {type(data).__name__}"
        )
    return hashlib.sha256(data).hexdigest()


def file_sha256(
    path: str | Path,
    *,
    block_size: int = DEFAULT_BLOCK_SIZE,
) -> str:
    """以分块读取方式计算文件 SHA-256，避免一次加载整个文件。"""
    if not isinstance(block_size, int) or isinstance(block_size, bool):
        raise TypeError(
            f"block_size 必须是 int，实际为 {type(block_size).__name__}"
        )
    if block_size <= 0:
        raise ValueError("block_size 必须大于 0")

    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(file_path)
    if not file_path.is_file():
        raise IsADirectoryError(file_path)

    digest = hashlib.sha256()

    with file_path.open("rb") as stream:
        while True:
            block = stream.read(block_size)
            if not block:
                break
            digest.update(block)

    return digest.hexdigest()


def normalize_text(text: str) -> str:
    """对文本进行保守的确定性规范化。

    规范化内容包括：

    - 移除文本开头的 UTF-8 BOM；
    - 将 CRLF 和 CR 换行统一为 LF；
    - 使用 Unicode NFC 规范化；
    - 删除每行末尾的空白；
    - 删除文本首尾的空行。

    不合并单词之间的空格，避免破坏代码和 Markdown 语义。
    """
    if not isinstance(text, str):
        raise TypeError(
            f"text 必须是 str，实际为 {type(text).__name__}"
        )

    normalized = text.removeprefix("\ufeff")
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = unicodedata.normalize("NFC", normalized)

    lines = [line.rstrip() for line in normalized.split("\n")]
    return "\n".join(lines).strip("\n")


def text_sha256(text: str) -> str:
    """计算规范化文本的 SHA-256。"""
    normalized = normalize_text(text)
    return sha256_bytes(normalized.encode("utf-8"))


def stable_id(
    namespace: str,
    *parts: str,
    digest_length: int = DEFAULT_ID_DIGEST_LENGTH,
) -> str:
    """根据命名空间和输入字段生成确定性 ID。

    使用长度前缀编码每个字段，避免以下输入产生相同序列：

    - ("ab", "c")
    - ("a", "bc")
    """
    if not isinstance(namespace, str):
        raise TypeError(
            f"namespace 必须是 str，实际为 {type(namespace).__name__}"
        )
    if _NAMESPACE_RE.fullmatch(namespace) is None:
        raise ValueError(
            "namespace 必须以小写字母开头，"
            "并且只能包含小写字母、数字和下划线"
        )

    if not parts:
        raise ValueError("stable_id 至少需要一个输入字段")

    if not isinstance(digest_length, int) or isinstance(
        digest_length,
        bool,
    ):
        raise TypeError(
            "digest_length 必须是 int，"
            f"实际为 {type(digest_length).__name__}"
        )
    if not 16 <= digest_length <= 64:
        raise ValueError("digest_length 必须位于 16 到 64 之间")

    payload = bytearray()
    namespace_bytes = namespace.encode("utf-8")
    payload.extend(len(namespace_bytes).to_bytes(8, "big"))
    payload.extend(namespace_bytes)

    for index, part in enumerate(parts):
        if not isinstance(part, str):
            raise TypeError(
                f"parts[{index}] 必须是 str，"
                f"实际为 {type(part).__name__}"
            )
        if not part:
            raise ValueError(f"parts[{index}] 不能为空")

        encoded = part.encode("utf-8")
        payload.extend(len(encoded).to_bytes(8, "big"))
        payload.extend(encoded)

    digest = hashlib.sha256(payload).hexdigest()
    return f"{namespace}_{digest[:digest_length]}"