from pprint import pprint
from typing import Any


def _preview(text: str, max_length: int = 160) -> str:
    text = (text or "").replace("\n", " ").strip()
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def _print_list(title: str, values: list[Any] | None) -> None:
    values = values or []
    print(f"{title}:")
    if not values:
        print("  []")
        return

    for index, value in enumerate(values, start=1):
        print(f"  [{index}] {value}")


def print_query_debug(query_info: dict | None) -> None:
    query_info = query_info or {}

    print("\nquery debug:")
    print(f"  query_type: {query_info.get('query_type')}")
    print(f"  retrieval_mode: {query_info.get('retrieval_mode')}")
    print(f"  need_retrieval: {query_info.get('need_retrieval')}")
    print(f"  need_rerank: {query_info.get('need_rerank')}")
    print(f"  use_sub_questions: {query_info.get('use_sub_questions')}")
    print(f"  top_k: {query_info.get('top_k')}")
    print(f"  rewrite_method: {query_info.get('rewrite_method')}")
    print(f"  original_query: {query_info.get('original_query')}")
    print(f"  normalized_query: {query_info.get('normalized_query')}")
    print(f"  rewritten_query: {query_info.get('rewritten_query')}")
    print(f"  route_reason: {query_info.get('route_reason')}")

    _print_list("  search_queries", query_info.get("search_queries"))
    _print_list("  sub_questions", query_info.get("sub_questions"))
    _print_list("  keywords", query_info.get("keywords"))


def print_retrieval_debug(retrieval_result: dict | None) -> None:
    retrieval_result = retrieval_result or {}

    print("\nretrieval debug:")
    if not retrieval_result:
        print("  retrieval_result: None")
        return

    print(f"  status: {retrieval_result.get('status')}")
    print(f"  retrieval_mode: {retrieval_result.get('retrieval_mode')}")
    print(f"  requested_retrieval_mode: {retrieval_result.get('requested_retrieval_mode')}")
    print(f"  fallback_reason: {retrieval_result.get('fallback_reason')}")
    print(f"  query: {retrieval_result.get('query')}")
    print(f"  top_k: {retrieval_result.get('top_k')}")
    print(f"  candidate_k: {retrieval_result.get('candidate_k')}")
    print(f"  per_query_k: {retrieval_result.get('per_query_k')}")

    rerank = retrieval_result.get("rerank") or {}
    print("  rerank:")
    if rerank:
        for key, value in rerank.items():
            print(f"    {key}: {value}")
    else:
        print("    None")

    _print_list("  executed_queries", retrieval_result.get("queries"))

    errors = retrieval_result.get("errors") or []
    print("  errors:")
    if not errors:
        print("    []")
    else:
        for error in errors:
            print(f"    - {error}")


def print_sources(sources: list[dict]) -> None:
    if not sources:
        print("\nsources: []")
        return

    print("\nsources:")
    for index, source in enumerate(sources, start=1):
        metadata = source.get("metadata", {})
        content = source.get("content", "")

        print(f"  [{index}]")
        print(f"      score: {source.get('score')}")
        print(f"      original_score: {source.get('original_score')}")
        print(f"      rerank_score: {source.get('rerank_score')}")
        print(f"      source_query: {source.get('source_query')}")
        print(f"      matched_queries: {source.get('matched_queries')}")
        print(f"      source: {metadata.get('source')}")
        print(f"      file_path: {metadata.get('file_path')}")
        print(f"      page: {metadata.get('page')}")
        print(f"      chunk_index: {metadata.get('chunk_index')}")
        print(f"      chunk_id: {metadata.get('chunk_id')}")
        print(f"      preview: {_preview(content)}")


def show_result(result: dict, question: str, show_raw_query_info: bool = False) -> None:
    print("=" * 80)
    print(f"question: {question}")

    print("\nstatus:")
    print(result.get("status"))

    print("\nanswer:")
    print(result.get("answer"))

    query_info = result.get("query_info")
    print_query_debug(query_info)

    if show_raw_query_info:
        print("\nraw query_info:")
        pprint(query_info)

    print_retrieval_debug(result.get("retrieval_result"))
    print_sources(result.get("sources", []))
