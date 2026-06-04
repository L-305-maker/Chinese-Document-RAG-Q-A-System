import argparse
import json
from pathlib import Path


RESULTS_DIR = Path(__file__).resolve().parent / "results"
METRICS = (
    "query_type_hit",
    "retrieval_mode_hit",
    "need_retrieval_hit",
    "source_hit",
    "passed",
)


def load_run(name: str) -> dict:
    run_dir = Path(name)
    if not run_dir.exists():
        run_dir = RESULTS_DIR / name

    summary_path = run_dir / "summary.json"
    eval_path = run_dir / "eval.jsonl"
    if not summary_path.exists():
        summary_path = run_dir / "latest_summary.json"
        eval_path = run_dir / "latest_eval.jsonl"

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    rows = {row["id"]: row for row in read_jsonl(eval_path)}

    return {
        "name": run_dir.name,
        "summary": summary,
        "rows": rows,
    }


def read_jsonl(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def show_metrics(before: dict, after: dict) -> None:
    print(f"compare: {before['name']} -> {after['name']}")
    print(f"total  : {before['summary'].get('total')} -> {after['summary'].get('total')}")
    print()

    for key in METRICS:
        old = before["summary"].get(key, 0)
        new = after["summary"].get(key, 0)
        print(f"{key:<20} {old:.1%} -> {new:.1%} ({new - old:+.1%})")


def show_cases(before: dict, after: dict, limit: int = 10) -> None:
    common_ids = set(before["rows"]) & set(after["rows"])
    before_failed = {sample_id for sample_id in common_ids if not before["rows"][sample_id].get("passed")}
    after_failed = {sample_id for sample_id in common_ids if not after["rows"][sample_id].get("passed")}

    groups = {
        "fixed": before_failed - after_failed,
        "new_failed": after_failed - before_failed,
        "still_failed": before_failed & after_failed,
    }

    print()
    for title, sample_ids in groups.items():
        print(f"{title}: {len(sample_ids)}")
        for sample_id in sorted(sample_ids)[:limit]:
            row = after["rows"].get(sample_id) or before["rows"][sample_id]
            print(f"- {sample_id}: {failed_checks(row)}")


def failed_checks(row: dict) -> str:
    checks = [key for key in METRICS[:-1] if row.get(key) is False]
    return ", ".join(checks) if checks else "passed"


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare saved evaluation results.")
    parser.add_argument("before", help="Old result folder name or path.")
    parser.add_argument("after", help="New result folder name or path.")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    before = load_run(args.before)
    after = load_run(args.after)

    show_metrics(before, after)
    show_cases(before, after, args.limit)


if __name__ == "__main__":
    main()
