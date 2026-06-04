from typing import Any


def show_result(result: dict[str, Any], question: str) -> None:
    query_info = result.get("query_info") or {}
    retrieval = result.get("retrieval_result") or {}
    sources = result.get("sources") or []

    print("=" * 80)
    print(f"question: {question}")
    print(f"status: {result.get('status')} | stage: {result.get('stage')}")

    if result.get("error") or result.get("error_type"):
        print(f"error: {result.get('error_type')} - {result.get('error')}")

    if result.get("answer") is not None:
        print(f"\nanswer:\n{result.get('answer')}")

    answer_validation = result.get("answer_validation") or {}
    if answer_validation:
        print("\nanswer_validation:")
        print(
            f"  status={answer_validation.get('answer_status')} "
            f"source_cited={answer_validation.get('source_cited')} "
            f"length={answer_validation.get('answer_length')}"
        )
        _print_list("  warnings", answer_validation.get("warnings"))
        _print_list("  errors", answer_validation.get("errors"))

    print("\nquery:")
    print(
        f"  type={query_info.get('query_type')} "
        f"mode={query_info.get('retrieval_mode')} "
        f"need_retrieval={query_info.get('need_retrieval')} "
        f"need_rerank={query_info.get('need_rerank')} "
        f"top_k={query_info.get('top_k')}"
    )
    print(f"  rewritten_query: {query_info.get('rewritten_query')}")
    _print_list("  search_queries", query_info.get("search_queries"))
    _print_list("  sub_questions", query_info.get("sub_questions"))

    print("\nretrieval:")
    if retrieval:
        rerank = retrieval.get("rerank") or {}
        print(
            f"  status={retrieval.get('status')} "
            f"mode={retrieval.get('retrieval_mode')} "
            f"top_k={retrieval.get('top_k')} "
            f"candidate_k={retrieval.get('candidate_k')} "
            f"docs={len(retrieval.get('documents') or [])}"
        )
        print(f"  rerank: status={rerank.get('status')} reason={rerank.get('reason')}")
        _print_list("  executed_queries", retrieval.get("queries"))
    else:
        print("  None")

    print(f"\nsources: {len(sources)}")
    for index, source in enumerate(sources, start=1):
        metadata = source.get("metadata") or {}
        score = source.get("rerank_score", source.get("score"))
        print(
            f"  [{index}] source={metadata.get('source')} "
            f"chunk={metadata.get('chunk_index')} "
            f"score={score}"
        )
        print(f"      preview={_preview(source.get('content', ''))}")


def _print_list(title: str, values: list[Any] | None) -> None:
    values = values or []
    if not values:
        print(f"{title}: []")
        return
    print(f"{title}: " + " | ".join(str(value) for value in values))


def _preview(text: str, max_length: int = 120) -> str:
    text = (text or "").replace("\n", " ").strip()
    return text if len(text) <= max_length else text[:max_length] + "..."
