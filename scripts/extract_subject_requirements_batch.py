from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from national_extraction_common import DATA_WORK, dump_json, extract_pdf_text, normalize_text, read_excel_rows, row_has_payload, detect_header_span, load_json
from remaining_extraction_support import (
    SUBJECT_NORMALIZED,
    SUBJECT_RAW,
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


def make_record(task: dict[str, Any], file_path: str) -> dict[str, Any]:
    return {
        "year": task.get("year"),
        "province": task.get("province", ""),
        "school_code": "",
        "school_name": "",
        "major_code": "",
        "major_name": "",
        "major_group_code": "",
        "major_group_name": "",
        "subject_requirement": "",
        "first_subject_requirement": "",
        "second_subject_requirement": "",
        "remarks": "",
        "source_file": file_path,
        "source_sheet": "",
        "source_page": None,
        "source_row": None,
        "extract_method": "",
        "confidence": "low",
    }


def parse_subject_task(task: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    raw_rows: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    target_fields = [
        "school_code",
        "school_name",
        "major_code",
        "major_name",
        "major_group_code",
        "major_group_name",
        "subject_requirement",
    ]
    for file_path in task["candidate_files"]:
        path = Path(file_path)
        if path.suffix.lower() in {".xls", ".xlsx"}:
            rows_by_sheet = read_excel_rows(path)
            for sheet_name, rows in rows_by_sheet.items():
                if not rows:
                    continue
                _, header_end, mapped = detect_header_span(rows, target_fields)
                if not mapped:
                    continue
                for idx, row in enumerate(rows[header_end + 1 :], start=header_end + 2):
                    if not row_has_payload(row):
                        continue
                    values = {field: row[col] if col < len(row) else "" for col, field in mapped.items()}
                    raw_rows.append({"source_file": str(path), "source_sheet": sheet_name, "source_row": idx, "values": values})
                    record = make_record(task, str(path))
                    for field in ["school_code", "school_name", "major_code", "major_name", "major_group_code", "major_group_name", "subject_requirement"]:
                        record[field] = normalize_text(values.get(field))
                    record["source_sheet"] = sheet_name
                    record["source_row"] = idx
                    record["extract_method"] = "excel_header_mapping"
                    record["confidence"] = "medium" if record["subject_requirement"] else "low"
                    if record["subject_requirement"]:
                        records.append(record)
        elif path.suffix.lower() == ".pdf":
            pages = extract_pdf_text(path, max_pages=5)
            for page in pages:
                page_no = page["page"]
                text = page.get("text") or ""
                for line_no, line in enumerate(text.splitlines(), start=1):
                    clean = normalize_text(line)
                    if not clean or not any(token in clean for token in ["不限", "物理", "历史", "化学", "生物", "政治", "地理"]):
                        continue
                    raw_rows.append({"source_file": str(path), "source_page": page_no, "source_row": line_no, "values": clean})
    return raw_rows, records


def run_single_task(task_id: str) -> int:
    task = next(task for task in load_remaining_tasks() if task["task_id"] == task_id)
    raw_rows, records = parse_subject_task(task)
    payload_path = TMP_DIR / f"{task_id}.json"
    dump_json(payload_path, {"raw_rows": raw_rows, "records": records})
    print(payload_path)
    return 0


def main() -> None:
    if len(sys.argv) == 3 and sys.argv[1] == "--single-task":
        raise SystemExit(run_single_task(sys.argv[2]))

    tasks = [task for task in load_remaining_tasks() if task["document_type"] == "subject_requirement"]
    init_progress(tasks)
    for task in tasks:
        output_path = SUBJECT_NORMALIZED / task_output_name(task)
        raw_path = SUBJECT_RAW / raw_output_name(task)
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
            update_task_status(task["task_id"], "failed", notes=(result.stderr or result.stdout or "unknown error")[:1000], output_file=str(output_path))
            maybe_write_progress_checkpoint()
            continue
        payload = load_json(payload_path)
        raw_rows, records = payload["raw_rows"], payload["records"]
        status = "needs_manual_review" if len(records) < 20 else "completed"
        dump_json(raw_path, raw_rows)
        dump_json(output_path, records)
        update_task_status(task["task_id"], status, records=len(records), output_file=str(output_path))
        maybe_write_progress_checkpoint()
    write_progress_markdown()
    print("Subject-requirement extraction complete")


if __name__ == "__main__":
    main()
