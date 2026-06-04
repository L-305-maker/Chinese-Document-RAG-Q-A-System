from typing import Any


MAX_CONTEXT_CHARS = 4000
MAX_DOC_CHARS = 1000


def build_context(
    documents: list[dict[str, Any]],
    max_context_chars: int = MAX_CONTEXT_CHARS,
    max_doc_chars: int = MAX_DOC_CHARS,
) -> str:
    parts = []
    used_chars = 0

    for index, doc in enumerate(documents, start=1):
        content = _truncate(doc.get("content", ""), max_doc_chars)
        if not content:
            continue

        block = _format_document(index, doc, content)
        if used_chars + len(block) > max_context_chars:
            break

        parts.append(block)
        used_chars += len(block)

    return "\n\n".join(parts)


def _format_document(index: int, doc: dict[str, Any], content: str) -> str:
    metadata = doc.get("metadata") or {}
    source = metadata.get("source", "unknown")
    chunk_index = metadata.get("chunk_index", "unknown")

    return (
        f"[资料 {index}]\n"
        f"来源: {source}\n"
        f"片段: {chunk_index}\n"
        f"内容:\n{content}"
    )


def _truncate(text: str, max_chars: int) -> str:
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "..."
