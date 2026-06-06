from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from extract_admissions_batch import extract_task as extract_admissions_task
from national_extraction_common import DATA_WORK, dump_json, load_json
from remaining_extraction_support import (
    REMAINING_ADMISSIONS_NORMALIZED,
    REMAINING_ADMISSIONS_RAW,
    cap_confidence,
    init_progress,
    is_valid_json_file,
    load_remaining_tasks,
    maybe_write_progress_checkpoint,
    raw_output_name,
    task_output_name,
    update_task_status,
    write_progress_markdown,
)

TIMEOUT_SECONDS = 300
TMP_DIR = DATA_WORK / "remaining_runtime"
TMP_DIR.mkdir(parents=True, exist_ok=True)


def postprocess_records(task: dict[str, Any], records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str]:
    needs_manual = False
    if task["priority"] == "low":
        for record in records:
            cap_confidence(record, "medium")
    if not task.get("province") or task.get("province") == "未知" or not task.get("subject_type") or task.get("subject_type") == "未知":
        for record in records:
            record["confidence"] = "low"
    min_score_filled = sum(1 for record in records if record.get("min_score") is not None)
    min_rank_filled = sum(1 for record in records if record.get("min_rank") is not None)
    if len(records) < 20:
        needs_manual = True
    if records and min_score_filled / len(records) < 0.3 and min_rank_filled / len(records) < 0.3:
        needs_manual = True
    return records, "needs_manual_review" if needs_manual else "completed"


def run_single_task(task_id: str) -> int:
    task = next(task for task in load_remaining_tasks() if task["task_id"] == task_id)
    raw_rows, records = extract_admissions_task(task)
    payload_path = TMP_DIR / f"{task_id}.json"
    dump_json(payload_path, {"raw_rows": raw_rows, "records": records})
    print(payload_path)
    return 0


def main() -> None:
    if len(sys.argv) == 3 and sys.argv[1] == "--single-task":
        raise SystemExit(run_single_task(sys.argv[2]))

    tasks = [task for task in load_remaining_tasks() if task["document_type"] == "admissions"]
    init_progress(tasks)
    for task in tasks:
        output_path = REMAINING_ADMISSIONS_NORMALIZED / task_output_name(task)
        raw_path = REMAINING_ADMISSIONS_RAW / raw_output_name(task)
        if is_valid_json_file(output_path):
            update_task_status(task["task_id"], "skipped_existing", output_file=str(output_path))
            maybe_write_progress_checkpoint()
            continue
        if task["requires_ocr"]:
            update_task_status(task["task_id"], "needs_ocr", output_file=str(output_path))
            maybe_write_progress_checkpoint()
            continue

        payload_path = TMP_DIR / f"{task['task_id']}.json"
        if payload_path.exists():
            payload_path.unlink()
        try:
            result = subprocess.run(
                [sys.executable, __file__, "--single-task", task["task_id"]],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired:
            update_task_status(task["task_id"], "timeout", notes="task exceeded 300 seconds", output_file=str(output_path))
            maybe_write_progress_checkpoint()
            continue
        if result.returncode != 0 or not payload_path.exists():
            notes = (result.stderr or result.stdout or "worker returned no payload").strip()
            update_task_status(task["task_id"], "failed", notes=notes[:1000], output_file=str(output_path))
            maybe_write_progress_checkpoint()
            continue
        payload = load_json(payload_path)
        raw_rows = payload["raw_rows"]
        records, status = postprocess_records(task, payload["records"])
        dump_json(raw_path, raw_rows)
        dump_json(output_path, records)
        update_task_status(task["task_id"], status, records=len(records), output_file=str(output_path))
        maybe_write_progress_checkpoint()

    write_progress_markdown()
    print("Remaining admissions extraction complete")


if __name__ == "__main__":
    main()
