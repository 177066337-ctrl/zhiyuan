from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import time

from national_extraction_common import DATA_WORK, dump_json, ensure_dir, iso_now, load_json, normalize_text, write_markdown

DOCS_DIR = Path("docs")
REMAINING_TASKS_PATH = DATA_WORK / "remaining_extraction_tasks.json"
PROGRESS_PATH = DATA_WORK / "remaining_extraction_progress.json"
FAILURES_PATH = DATA_WORK / "remaining_extraction_failures.json"

REMAINING_ADMISSIONS_RAW = ensure_dir(DATA_WORK / "remaining_admissions_raw")
REMAINING_ADMISSIONS_NORMALIZED = ensure_dir(DATA_WORK / "remaining_admissions_normalized")
REMAINING_RANK_RAW = ensure_dir(DATA_WORK / "remaining_rank_tables_raw")
REMAINING_RANK_NORMALIZED = ensure_dir(DATA_WORK / "remaining_rank_tables_normalized")
PLANS_RAW = ensure_dir(DATA_WORK / "plans_raw")
PLANS_NORMALIZED = ensure_dir(DATA_WORK / "plans_normalized")
SUBJECT_RAW = ensure_dir(DATA_WORK / "subject_requirements_raw")
SUBJECT_NORMALIZED = ensure_dir(DATA_WORK / "subject_requirements_normalized")


def task_output_name(task: dict[str, Any]) -> str:
    province = task.get("province") or "unknown"
    year = task.get("year") or "unknown"
    subject_type = task.get("subject_type") or "unknown"
    batch = task.get("batch") or "all"
    document_type = task.get("document_type") or "unknown"
    if document_type == "rank_table":
        return f"{province}_{year}_{subject_type}.normalized.json"
    return f"{province}_{year}_{subject_type}_{batch}.normalized.json"


def raw_output_name(task: dict[str, Any]) -> str:
    return task_output_name(task).replace(".normalized.json", ".raw.json")


def output_dir_for_task(task: dict[str, Any], normalized: bool = True) -> Path:
    doc_type = task.get("document_type")
    if doc_type == "admissions":
        return REMAINING_ADMISSIONS_NORMALIZED if normalized else REMAINING_ADMISSIONS_RAW
    if doc_type == "rank_table":
        return REMAINING_RANK_NORMALIZED if normalized else REMAINING_RANK_RAW
    if doc_type == "plans":
        return PLANS_NORMALIZED if normalized else PLANS_RAW
    if doc_type == "subject_requirement":
        return SUBJECT_NORMALIZED if normalized else SUBJECT_RAW
    raise ValueError(f"unsupported document type: {doc_type}")


def is_valid_json_file(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        json.loads(path.read_text(encoding="utf-8"))
        return True
    except Exception:
        return False


def load_remaining_tasks() -> list[dict[str, Any]]:
    return load_json(REMAINING_TASKS_PATH) if REMAINING_TASKS_PATH.exists() else []


def init_progress(tasks: list[dict[str, Any]]) -> None:
    if PROGRESS_PATH.exists():
        return
    payload = {
        "generated_at": iso_now(),
        "updated_at": iso_now(),
        "total_tasks": len(tasks),
        "tasks": [
            {
                "task_id": task["task_id"],
                "document_type": task["document_type"],
                "province": task.get("province", ""),
                "year": task.get("year", ""),
                "subject_type": task.get("subject_type", ""),
                "batch": task.get("batch", ""),
                "planned_action": task.get("planned_action", ""),
                "status": task.get("status", "pending"),
                "output_file": task.get("output_file", ""),
                "records": 0,
                "risk_level": task.get("risk_level", ""),
                "notes": "",
            }
            for task in tasks
        ],
    }
    save_state_json(PROGRESS_PATH, payload)
    if not FAILURES_PATH.exists():
        save_state_json(FAILURES_PATH, [])


def save_state_json(path: Path, data: Any) -> None:
    ensure_dir(path.parent)
    text = json.dumps(data, ensure_ascii=False, indent=2)
    last_error: Exception | None = None
    for _ in range(5):
        try:
            path.write_text(text, encoding="utf-8")
            return
        except Exception as exc:
            last_error = exc
            time.sleep(0.05)
    if last_error is not None:
        raise last_error


def update_task_status(task_id: str, status: str, *, records: int = 0, notes: str = "", output_file: str = "") -> None:
    progress = load_json(PROGRESS_PATH)
    for task in progress["tasks"]:
        if task["task_id"] == task_id:
            task["status"] = status
            task["records"] = records
            task["notes"] = notes
            if output_file:
                task["output_file"] = output_file
            break
    progress["updated_at"] = iso_now()
    save_state_json(PROGRESS_PATH, progress)
    if status in {"failed", "timeout"}:
        failures = load_json(FAILURES_PATH)
        failures.append(
            {
                "task_id": task_id,
                "status": status,
                "records": records,
                "notes": notes,
                "output_file": output_file,
                "updated_at": iso_now(),
            }
        )
        save_state_json(FAILURES_PATH, failures)


def progress_summary() -> dict[str, Any]:
    progress = load_json(PROGRESS_PATH)
    tasks = progress["tasks"]
    status_counter = Counter(task["status"] for task in tasks)
    doc_counter = Counter(task["document_type"] for task in tasks)
    province_counter = Counter(task["province"] for task in tasks)
    return {
        "total_tasks": len(tasks),
        "status_counts": dict(status_counter),
        "document_type_counts": dict(doc_counter),
        "province_counts": dict(province_counter),
        "tasks": tasks,
    }


def write_progress_markdown() -> None:
    summary = progress_summary()
    status_counts = summary["status_counts"]
    doc_counts = summary["document_type_counts"]
    province_counts = summary["province_counts"]
    top_provinces = sorted(province_counts.items(), key=lambda item: (-item[1], item[0]))[:30]
    lines = [
        "# Remaining Extraction Progress",
        "",
        f"- Generated/updated: {iso_now()}",
        f"- 剩余任务总数: {summary['total_tasks']}",
        f"- 已完成数量: {status_counts.get('completed', 0)}",
        f"- 跳过数量: {status_counts.get('skipped_existing', 0)}",
        f"- 失败数量: {status_counts.get('failed', 0)}",
        f"- timeout 数量: {status_counts.get('timeout', 0)}",
        f"- needs_ocr 数量: {status_counts.get('needs_ocr', 0)}",
        f"- needs_manual_review 数量: {status_counts.get('needs_manual_review', 0)}",
        "",
        "## 按 document_type 统计",
    ]
    for key, value in sorted(doc_counts.items()):
        lines.append(f"- {key}: {value}")
    lines += [
        "",
        "## 按 province 统计",
    ]
    for province, count in top_provinces:
        lines.append(f"- {province}: {count}")
    lines += [
        "",
        "## 下一步建议",
        "- 优先校验 completed 和 needs_manual_review 的结果，再决定是否进入总体验证和前端候选筛选。",
    ]
    write_markdown(DOCS_DIR / "remaining_extraction_progress.md", "\n".join(lines))


def maybe_write_progress_checkpoint() -> None:
    summary = progress_summary()
    processed = sum(
        summary["status_counts"].get(key, 0)
        for key in ["completed", "skipped_existing", "failed", "timeout", "needs_ocr", "needs_manual_review"]
    )
    if processed and processed % 20 == 0:
        write_progress_markdown()


def cap_confidence(record: dict[str, Any], ceiling: str) -> dict[str, Any]:
    order = {"low": 0, "medium": 1, "high": 2}
    current = normalize_text(record.get("confidence")) or "low"
    if order.get(current, 0) > order.get(ceiling, 0):
        record["confidence"] = ceiling
    return record
