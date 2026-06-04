from typing import Any


INSUFFICIENT_CONTEXT_PHRASES = (
    "根据现有资料无法回答",
    "参考资料不足",
    "资料不足",
    "无法回答",
)
MIN_ANSWER_LENGTH = 20


def validate_answer(
    answer: Any,
    documents: list[dict[str, Any]] | dict[str, Any] | None = None,
    min_answer_length: int = MIN_ANSWER_LENGTH,
    require_sources: bool = True,
) -> dict[str, Any]:
    docs = _normalize_documents(documents)
    text = "" if answer is None else str(answer).strip()

    if not text:
        return {
            "answer_status": "failed",
            "source_cited": False,
            "answer_length": 0,
            "document_count": len(docs),
            "cited_sources": [],
            "warnings": [],
            "errors": ["empty_answer"],
        }

    source_cited, cited_sources = _check_source_cited(text, docs)

    if _contains_any(text, INSUFFICIENT_CONTEXT_PHRASES):
        return {
            "answer_status": "insufficient_context",
            "source_cited": source_cited,
            "answer_length": len(text),
            "document_count": len(docs),
            "cited_sources": cited_sources,
            "warnings": [],
            "errors": [],
        }

    warnings = []
    if docs and not source_cited:
        warnings.append("missing_source_reference")
    if require_sources and not docs:
        warnings.append("no_documents_but_answered")
    if len(text) < min_answer_length:
        warnings.append("answer_too_short")

    return {
        "answer_status": "warning" if warnings else "passed",
        "source_cited": source_cited,
        "answer_length": len(text),
        "document_count": len(docs),
        "cited_sources": cited_sources,
        "warnings": warnings,
        "errors": [],
    }


def _normalize_documents(documents: list[dict[str, Any]] | dict[str, Any] | None) -> list[dict[str, Any]]:
    if documents is None:
        return []
    if isinstance(documents, dict):
        return [documents]
    return documents


def _check_source_cited(answer: str, documents: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    cited_sources = []

    for index, doc in enumerate(documents, start=1):
        source = _get_source(doc)
        aliases = _source_aliases(source, index)

        if any(alias and alias in answer for alias in aliases):
            cited_sources.append(source or f"资料 {index}")

    return bool(cited_sources), cited_sources


def _get_source(document: dict[str, Any]) -> str:
    metadata = document.get("metadata") or {}
    return str(metadata.get("source") or "").strip()


def _source_aliases(source: str, index: int) -> set[str]:
    file_name = source.replace("\\", "/").split("/")[-1]
    file_stem = file_name.rsplit(".", 1)[0] if "." in file_name else file_name

    return {
        source,
        file_name,
        file_stem,
        f"资料 {index}",
        f"[资料 {index}]",
    }


def _contains_any(text: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in text for phrase in phrases)
