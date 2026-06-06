from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from extract_admissions_batch import extract_task
from national_extraction_common import DATA_WORK, dump_json, ensure_dir, load_json

RAW_DIR = ensure_dir(DATA_WORK / "backfill_admissions_raw")
NORMALIZED_DIR = ensure_dir(DATA_WORK / "backfill_admissions_normalized")
SUMMARY_PATH = DATA_WORK / "score_lookup_backfill_admissions_summary.json"


def file_base(task: dict[str, Any]) -> str:
    return f"{task.get('province') or 'unknown'}_{task.get('year') or 'unknown'}_{task.get('subject_type') or 'unknown'}_{task.get('batch') or 'all'}"


def has_valid_existing(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        data = load_json(path)
    except Exception:
        return False
    return isinstance(data, list)


def main() -> None:
    backfill_tasks = load_json(DATA_WORK / "score_lookup_backfill_tasks.json")
    extraction_tasks = {task["task_id"]: task for task in load_json(DATA_WORK / "extraction_tasks.json")}
    targets = [
        task
        for task in backfill_tasks
        if task["missing_type"] in {"admissions", "both"}
        and task["planned_action"] == "extract_admissions"
        and task["priority"] in {"high", "medium"}
        and not task["requires_ocr"]
        and not task["requires_manual_review"]
    ]

    rows = []
    counts: Counter[str] = Counter()
    for task in targets:
        base = file_base(task)
        raw_path = RAW_DIR / f"{base}.raw.json"
        normalized_path = NORMALIZED_DIR / f"{base}.normalized.json"
        if has_valid_existing(raw_path) and has_valid_existing(normalized_path):
            counts["skipped_existing"] += 1
            rows.append({"task_id": task["task_id"], "status": "skipped_existing", "records": len(load_json(normalized_path)), "output_file": str(normalized_path)})
            continue

        merged_raw: list[dict[str, Any]] = []
        merged_records: list[dict[str, Any]] = []
        for source_id in task.get("source_task_ids", []):
            source_task = extraction_tasks.get(source_id)
            if not source_task:
                continue
            task_for_extract = dict(source_task)
            task_for_extract["province"] = task["province"]
            task_for_extract["year"] = task["year"]
            task_for_extract["subject_type"] = task["subject_type"]
            task_for_extract["batch"] = task["batch"]
            raw_rows, records = extract_task(task_for_extract)
            merged_raw.extend(raw_rows)
            merged_records.extend(records)

        if not merged_raw and not merged_records:
            counts["failed"] += 1
            rows.append({"task_id": task["task_id"], "status": "failed", "records": 0, "output_file": str(normalized_path)})
            continue

        dump_json(raw_path, merged_raw)
        dump_json(normalized_path, merged_records)
        status = "completed"
        if len(merged_records) < 100:
            status = "needs_manual_review"
        counts[status] += 1
        rows.append({"task_id": task["task_id"], "status": status, "records": len(merged_records), "output_file": str(normalized_path)})

    dump_json(SUMMARY_PATH, {"total": len(targets), "counts": dict(counts), "rows": rows})
    print(f"backfill admissions: total={len(targets)}, completed={counts['completed']}, manual_review={counts['needs_manual_review']}, failed={counts['failed']}")


if __name__ == "__main__":
    main()
