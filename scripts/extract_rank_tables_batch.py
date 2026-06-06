from __future__ import annotations

import re
from pathlib import Path

from national_extraction_common import (
    DATA_WORK,
    DOC_RANK,
    classify_confidence,
    dump_json,
    ensure_dir,
    extract_pdf_text,
    normalize_text,
    read_excel_rows,
    row_has_payload,
    safe_float,
    safe_int,
    load_json,
    detect_header_span,
)


RAW_DIR = ensure_dir(DATA_WORK / "national_rank_tables_raw")
NORMALIZED_DIR = ensure_dir(DATA_WORK / "national_rank_tables_normalized")


def make_record(task: dict, file_path: str) -> dict:
    return {
        "year": safe_int(task.get("year")),
        "province": task.get("province", ""),
        "subject_type": task.get("subject_type", ""),
        "score": None,
        "same_score_count": None,
        "cumulative_count": None,
        "rank": None,
        "source_file": file_path,
        "source_sheet": "",
        "source_page": None,
        "source_row": None,
        "extract_method": "",
        "confidence": "low",
    }


def parse_excel_rank_tables(path: Path, task: dict) -> tuple[list[dict], list[dict]]:
    raw_rows: list[dict] = []
    records: list[dict] = []
    rows_by_sheet = read_excel_rows(path)
    target_fields = ["score", "same_score_count", "cumulative_count", "rank"]

    for sheet_name, rows in rows_by_sheet.items():
        if not rows:
            continue
        header_start, header_end, mapped = detect_header_span(rows, target_fields)
        if not mapped:
            continue
        for idx, row in enumerate(rows[header_end + 1 :], start=header_end + 2):
            if not row_has_payload(row):
                continue
            values = {}
            for col, field in mapped.items():
                values[field] = row[col] if col < len(row) else ""
            raw_rows.append(
                {
                    "source_file": str(path),
                    "source_sheet": sheet_name,
                    "source_row": idx,
                    "values": values,
                }
            )
            score = safe_float(values.get("score"))
            same_score_count = safe_int(values.get("same_score_count"))
            cumulative_count = safe_int(values.get("cumulative_count"))
            rank = safe_int(values.get("rank")) or cumulative_count
            if score is None:
                continue
            record = make_record(task, str(path))
            record["score"] = score
            record["same_score_count"] = same_score_count
            record["cumulative_count"] = cumulative_count
            record["rank"] = rank
            record["source_sheet"] = sheet_name
            record["source_row"] = idx
            record["extract_method"] = "excel_header_mapping"
            record["confidence"] = classify_confidence(
                school_name="rank_table",
                score=record["score"],
                rank=record["rank"],
            )
            records.append(record)
    return raw_rows, records


def parse_pdf_rank_line(line: str) -> dict | None:
    text = normalize_text(line)
    if not text:
        return None
    if any(keyword in text for keyword in ["\u4e00\u5206\u4e00\u6bb5", "\u7edf\u8ba1\u8868", "\u5206\u6570\u6bb5", "\u8bf4\u660e"]):
        return None
    nums = re.findall(r"\d+(?:\.\d+)?", text)
    if len(nums) < 2:
        return None
    score = safe_float(nums[0])
    if score is None or score > 1000:
        return None
    same_score_count = safe_int(nums[1]) if len(nums) >= 2 else None
    cumulative_count = safe_int(nums[2]) if len(nums) >= 3 else None
    rank = safe_int(nums[3]) if len(nums) >= 4 else cumulative_count
    return {
        "score": score,
        "same_score_count": same_score_count,
        "cumulative_count": cumulative_count,
        "rank": rank,
    }


def parse_pdf_rank_tables(path: Path, task: dict) -> tuple[list[dict], list[dict]]:
    raw_rows: list[dict] = []
    records: list[dict] = []
    pages = extract_pdf_text(path)
    for page in pages:
        page_no = page["page"]
        tables = page.get("tables") or []
        for row_index, table in enumerate(tables, start=1):
            for inner_index, row in enumerate(table or [], start=1):
                clean = [normalize_text(cell) for cell in row]
                joined = " ".join(clean)
                parsed = parse_pdf_rank_line(joined)
                if not parsed:
                    continue
                raw_rows.append(
                    {
                        "source_file": str(path),
                        "source_page": page_no,
                        "source_row": inner_index,
                        "values": clean,
                    }
                )
                record = make_record(task, str(path))
                record.update(parsed)
                record["source_page"] = page_no
                record["source_row"] = inner_index
                record["extract_method"] = "pdf_table"
                record["confidence"] = classify_confidence(
                    school_name="rank_table",
                    score=record["score"],
                    rank=record["rank"],
                )
                records.append(record)
        text = page.get("text") or ""
        for line_no, line in enumerate(text.splitlines(), start=1):
            parsed = parse_pdf_rank_line(line)
            if not parsed:
                continue
            raw_rows.append(
                {
                    "source_file": str(path),
                    "source_page": page_no,
                    "source_row": line_no,
                    "values": parsed,
                }
            )
            record = make_record(task, str(path))
            record.update(parsed)
            record["source_page"] = page_no
            record["source_row"] = line_no
            record["extract_method"] = "pdf_line_parser"
            record["confidence"] = classify_confidence(
                school_name="rank_table",
                score=record["score"],
                rank=record["rank"],
            )
            records.append(record)
    return raw_rows, records


def extract_task(task: dict) -> tuple[list[dict], list[dict]]:
    all_raw: list[dict] = []
    all_records: list[dict] = []
    for file_path in task["candidate_files"]:
        path = Path(file_path)
        try:
            if path.suffix.lower() in {".xls", ".xlsx"}:
                raw_rows, records = parse_excel_rank_tables(path, task)
            elif path.suffix.lower() == ".pdf":
                raw_rows, records = parse_pdf_rank_tables(path, task)
            else:
                continue
        except Exception as exc:
            all_raw.append(
                {
                    "source_file": str(path),
                    "error": str(exc),
                    "values": {},
                }
            )
            continue
        all_raw.extend(raw_rows)
        all_records.extend(records)
    return all_raw, all_records


def out_name(task: dict) -> str:
    province = task.get("province") or "unknown"
    year = task.get("year") or "unknown"
    subject_type = task.get("subject_type") or "unknown"
    return f"{province}_{year}_{subject_type}"


def main() -> None:
    tasks = load_json(DATA_WORK / "extraction_tasks.json")
    target_tasks = [
        task
        for task in tasks
        if task["document_type"] == DOC_RANK
        and task["priority"] in {"high", "medium"}
        and not task["requires_ocr"]
        and task["selected"]
    ]
    processed = 0
    for task in target_tasks:
        raw_rows, records = extract_task(task)
        base = out_name(task)
        dump_json(RAW_DIR / f"{base}.raw.json", raw_rows)
        dump_json(NORMALIZED_DIR / f"{base}.normalized.json", records)
        processed += 1
        print(f"[rank] {task['task_id']} -> {len(records)} records")
    print(f"Processed {processed} rank-table tasks")


if __name__ == "__main__":
    main()

