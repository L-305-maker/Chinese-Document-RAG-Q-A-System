import json
from pathlib import Path
from datetime import datetime
import argparse
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config.setting import settings
from src.query_processing.process_query import process_query
from utils.read_jsonl import read_data
from utils.show_results import show_result
from utils.ensure_dir import ensure_dir


def evaluate_sample(sample: dict[str, Any], retriever: Any) -> dict[str, Any]:
    question = sample["question"]

    try:
        query_info = process_query(question)
        retrieval = None
        sources = []
        status = "success"
        stage = "process_query"

        if query_info.get("status") == "invalid query":
            status = "error"
        elif query_info.get("need_retrieval", True):
            stage = "retrieve"
            retrieval = retriever.retrieve_with_route(query_info)
            sources = retrieval.get("documents", [])
            status = retrieval.get("status", "error")
        else:
            stage = "route_no_retrieval"
            retrieval = {
                "status": "success",
                "retrieval_mode": query_info.get("retrieval_mode"),
                "documents": [],
            }

        answer = {
            "status": status,
            "stage": stage,
            "answer": None,
            "query_info": query_info,
            "retrieval_result": retrieval,
            "sources": sources,
        }

    except Exception as exc:
        answer = {
            "status": "error",
            "stage": "eval",
            "answer": None,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "query_info": {"original_query": question},
            "retrieval_result": None,
            "sources": [],
        }

    query_info = answer.get("query_info") or {}
    actual_sources = [
        source["metadata"]["source"]
        for source in answer.get("sources", [])
        if source.get("metadata", {}).get("source")
    ]
    expected_sources = sample.get("expected_sources") or []
    checks = {
        "query_type_hit": query_info.get("query_type") == sample.get("expected_query_type"),
        "retrieval_mode_hit": query_info.get("retrieval_mode") == sample.get("expected_retrieval_mode"),
        "need_retrieval_hit": query_info.get("need_retrieval") == sample.get("expected_need_retrieval"),
        "source_hit": not actual_sources if not expected_sources else any(source in actual_sources for source in expected_sources),
    }

    return {
        "id": sample.get("id"),
        "question": question,
        "answer": answer,
        "actual_sources": actual_sources,
        "expected_sources": expected_sources,
        **checks,
        "passed": all(checks.values()),
    }


def eval_file(
    file_path: str,
    limit: int | None = None,
    verbose: bool = True,
    failed_only: bool = False,
) -> list[dict[str, Any]]:
    samples = read_data(file_path)
    samples = samples[:limit] if limit is not None else samples
    if not samples:
        return []

    from src.retrieval.retriever import VectorRetriever
    from src.vectorstore.chroma_store import ChromaVectorStore

    retriever = VectorRetriever(vector_store=ChromaVectorStore())
    results = [evaluate_sample(sample, retriever) for sample in samples]

    if verbose:
        for result in results:
            if failed_only and result["passed"]:
                continue
            show_result(result["answer"], result["question"])
            print(
                f"eval: {'PASS' if result['passed'] else 'FAIL'} "
                f"query={result['query_type_hit']} "
                f"mode={result['retrieval_mode_hit']} "
                f"need_retrieval={result['need_retrieval_hit']} "
                f"source={result['source_hit']}"
            )
            print(f"expected_sources: {result['expected_sources']}")
            print(f"actual_sources: {result['actual_sources']}")

    return results


def build_summary(results: list[dict[str, Any]], config: dict[str, Any] | None = None) -> dict[str, Any]:
    failed = [result for result in results if not result["passed"]]
    return {
        "total": len(results),
        "query_type_hit": _rate(results, "query_type_hit"),
        "retrieval_mode_hit": _rate(results, "retrieval_mode_hit"),
        "need_retrieval_hit": _rate(results, "need_retrieval_hit"),
        "source_hit": _rate(results, "source_hit"),
        "passed": _rate(results, "passed"),
        "failed_cases": [
            {
                "id": result["id"],
                "question": result["question"],
                "stage": result["answer"].get("stage"),
                "status": result["answer"].get("status"),
            }
            for result in failed
        ],
        "config": config or {},
    }


def print_summary(summary: dict[str, Any]) -> None:
    print("=" * 20, "summary", "=" * 20)
    print(f"total: {summary['total']}")
    for key in ("query_type_hit", "retrieval_mode_hit", "need_retrieval_hit", "source_hit", "passed"):
        print(f"{key}: {summary[key]:.2%}")

    print(f"failed_cases: {len(summary['failed_cases'])}")
    for result in summary["failed_cases"][:10]:
        print(f"- {result['id']}: {result['question']} (stage={result['stage']}, status={result['status']})")


def save_report(results: list[dict[str, Any]], summary: dict[str, Any], output_dir: str) -> None:
    output_path = Path(output_dir)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = ensure_dir(output_path / timestamp)
    latest_dir = ensure_dir(output_path / "latest_evaluation")

    eval_path = run_dir / "eval.jsonl"
    summary_path = run_dir / "summary.json"
    latest_eval_path = latest_dir / "latest_eval.jsonl"
    latest_summary_path = latest_dir / "latest_summary.json"

    _write_jsonl(eval_path, results)
    _write_jsonl(latest_eval_path, results)

    _write_json(summary_path, summary)
    _write_json(latest_summary_path, summary)

    print(f"saved_eval: {eval_path}")
    print(f"saved_summary: {summary_path}")
    print(f"saved_latest_eval: {latest_eval_path}")
    print(f"saved_latest_summary: {latest_summary_path}")


def build_run_config(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "eval_file": args.file,
        "limit": args.limit,
        "quiet": args.quiet,
        "failed_only": args.failed_only,
        "output_dir": args.output_dir,
        "vector_db_path": settings.VECTOR_DB_PATH,
        "collection_name": settings.COLLECTION_NAME,
        "embedding_model": settings.EMBEDDING_MODEL,
        "embedding_device": settings.EMBEDDING_DEVICE,
        "rerank_enabled": settings.RERANK_ENABLED,
        "rerank_allow_download": settings.RERANK_ALLOW_DOWNLOAD,
        "rerank_model": settings.RERANK_MODEL,
        "rerank_candidate_multiplier": settings.RERANK_CANDIDATE_MULTIPLIER,
        "rerank_max_candidates": settings.RERANK_MAX_CANDIDATES,
        "multi_query_max_queries": settings.MULTI_QUERY_MAX_QUERIES,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _rate(results: list[dict[str, Any]], key: str) -> float:
    return sum(1 for result in results if result.get(key)) / len(results) if results else 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a minimal retrieval evaluation demo.")
    parser.add_argument("--file", default="evaluation/qs_eval.jsonl")
    parser.add_argument("--limit", type=int, default=3)
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--failed-only", action="store_true")
    parser.add_argument("--output-dir", default="evaluation/results")
    parser.add_argument("--no-save", action="store_true")
    args = parser.parse_args()

    results = eval_file(
        args.file,
        limit=args.limit,
        verbose=not args.quiet,
        failed_only=args.failed_only,
    )
    summary = build_summary(results, config=build_run_config(args))
    print_summary(summary)

    if not args.no_save:
        save_report(results, summary, args.output_dir)


if __name__ == "__main__":
    main()
