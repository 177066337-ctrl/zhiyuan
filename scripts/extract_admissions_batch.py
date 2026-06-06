from __future__ import annotations

import re
from pathlib import Path

from national_extraction_common import (
    DATA_WORK,
    DOC_ADMISSIONS,
    classify_confidence,
    detect_batch,
    detect_province,
    detect_subject_type,
    detect_year,
    dump_json,
    ensure_dir,
    extract_pdf_text,
    normalize_text,
    read_excel_rows,
    row_has_payload,
    safe_float,
    safe_int,
    split_school_group_text,
    load_json,
    detect_header_span,
)


RAW_DIR = ensure_dir(DATA_WORK / "national_admissions_raw")
NORMALIZED_DIR = ensure_dir(DATA_WORK / "national_admissions_normalized")


def make_record(task: dict, file_path: str) -> dict:
    return {
        "year": safe_int(task.get("year")),
        "province": task.get("province", ""),
        "subject_type": task.get("subject_type", ""),
        "batch": task.get("batch", ""),
        "school_code": "",
        "school_name": "",
        "major_group_code": "",
        "major_group_name": "",
        "major_code": "",
        "major_name": "",
        "min_score": None,
        "min_rank": None,
        "avg_score": None,
        "max_score": None,
        "plan_count": None,
        "admission_count": None,
        "remarks": "",
        "source_file": file_path,
        "source_sheet": "",
        "source_page": None,
        "source_row": None,
        "extract_method": "",
        "confidence": "low",
    }


def parse_excel_admissions(path: Path, task: dict) -> tuple[list[dict], list[dict]]:
    raw_rows: list[dict] = []
    records: list[dict] = []
    rows_by_sheet = read_excel_rows(path)
    target_fields = [
        "school_code",
        "school_name",
        "major_group_name",
        "major_name",
        "min_score",
        "min_rank",
        "avg_score",
        "max_score",
        "plan_count",
        "admission_count",
    ]

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
            record = make_record(task, str(path))
            school_text = normalize_text(values.get("school_name"))
            school_name, group_from_text = split_school_group_text(school_text)
            record["school_code"] = normalize_text(values.get("school_code"))
            record["school_name"] = school_name or school_text
            record["major_group_name"] = normalize_text(values.get("major_group_name")) or group_from_text
            record["major_group_code"] = normalize_text(values.get("major_group_code"))
            record["major_code"] = normalize_text(values.get("major_code"))
            record["major_name"] = normalize_text(values.get("major_name"))
            record["min_score"] = safe_float(values.get("min_score"))
            record["min_rank"] = safe_int(values.get("min_rank"))
            record["avg_score"] = safe_float(values.get("avg_score"))
            record["max_score"] = safe_float(values.get("max_score"))
            record["plan_count"] = safe_int(values.get("plan_count"))
            record["admission_count"] = safe_int(values.get("admission_count"))
            record["source_sheet"] = sheet_name
            record["source_row"] = idx
            record["extract_method"] = "excel_header_mapping"
            record["remarks"] = ""
            record["confidence"] = classify_confidence(
                school_name=record["school_name"],
                score=record["min_score"],
                rank=record["min_rank"],
            )
            if (
                not record["school_name"]
                and not record["major_name"]
                and record["min_score"] is None
                and record["min_rank"] is None
            ):
                continue
            records.append(record)
    return raw_rows, records


def parse_pdf_line(line: str, state: dict) -> dict | None:
    text = normalize_text(line)
    if not text:
        return None
    if any(keyword in text for keyword in ["\u8bf4\u660e", "\u672a\u6295\u6863", "\u7b2c", "\u6279\u6b21"]):
        return None
    if re.match(r"^\d{4}\s+", text):
        match = re.match(
            r"^(?P<school_code>\d{4})\s+(?P<school_name>.+?)\s+(?P<subject_type>\S+)\s+(?P<group>\S+)\s+(?P<score>\d{2,3}(?:\.\d{1,9})?)$",
            text,
        )
        if match:
            state["school_code"] = match.group("school_code")
            state["school_name"] = match.group("school_name")
            return {
                "school_code": match.group("school_code"),
                "school_name": match.group("school_name"),
                "subject_type": match.group("subject_type"),
                "major_group_name": match.group("group"),
                "min_score": safe_float(match.group("score")),
            }
    if state.get("school_name"):
        match = re.match(
            r"^(?P<subject_type>\S+)\s+(?P<group>\S+)\s+(?P<score>\d{2,3}(?:\.\d{1,9})?)$",
            text,
        )
        if match:
            return {
                "school_code": state.get("school_code", ""),
                "school_name": state.get("school_name", ""),
                "subject_type": match.group("subject_type"),
                "major_group_name": match.group("group"),
                "min_score": safe_float(match.group("score")),
            }
    numbers = re.findall(r"\d+(?:\.\d+)?", text)
    if len(numbers) >= 3 and re.search(r"[\u4e00-\u9fff]{2,}", text):
        return None
    return None


def parse_pdf_admissions(path: Path, task: dict) -> tuple[list[dict], list[dict]]:
    raw_rows: list[dict] = []
    records: list[dict] = []
    pages = extract_pdf_text(path)
    state: dict = {}

    for page in pages:
        page_no = page["page"]
        tables = page.get("tables") or []
        for table in tables:
            for row_index, row in enumerate(table or [], start=1):
                clean = [normalize_text(cell) for cell in row]
                joined = " ".join(clean)
                if not re.search(r"\d", joined):
                    continue
                if any(keyword in joined for keyword in ["\u9662\u6821", "\u6295\u6863", "\u6700\u4f4e\u5206", "\u5e8f\u53f7"]):
                    continue
                raw_rows.append(
                    {
                        "source_file": str(path),
                        "source_page": page_no,
                        "source_row": row_index,
                        "values": clean,
                    }
                )
                if len(clean) >= 5:
                    record = make_record(task, str(path))
                    record["school_code"] = clean[0] if re.fullmatch(r"\d{3,6}", clean[0]) else ""
                    record["school_name"] = clean[1] if len(clean) > 1 else ""
                    record["major_group_code"] = clean[2] if len(clean) > 2 and re.search(r"[A-Z0-9]", clean[2]) else ""
                    record["major_group_name"] = clean[3] if len(clean) > 3 else ""
                    record["min_score"] = safe_float(clean[4] if len(clean) > 4 else None)
                    record["min_rank"] = safe_int(clean[5] if len(clean) > 5 else None)
                    record["source_page"] = page_no
                    record["source_row"] = row_index
                    record["extract_method"] = "pdf_table"
                    record["confidence"] = classify_confidence(
                        school_name=record["school_name"],
                        score=record["min_score"],
                        rank=record["min_rank"],
                    )
                    if record["school_name"] or record["min_score"] is not None or record["min_rank"] is not None:
                        records.append(record)

        text = page.get("text") or ""
        for line_no, line in enumerate(text.splitlines(), start=1):
            parsed = parse_pdf_line(line, state)
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
            record["school_code"] = normalize_text(parsed.get("school_code"))
            record["school_name"] = normalize_text(parsed.get("school_name"))
            record["major_group_name"] = normalize_text(parsed.get("major_group_name"))
            record["min_score"] = safe_float(parsed.get("min_score"))
            record["subject_type"] = normalize_text(parsed.get("subject_type")) or record["subject_type"]
            record["source_page"] = page_no
            record["source_row"] = line_no
            record["extract_method"] = "pdf_line_parser"
            record["confidence"] = classify_confidence(
                school_name=record["school_name"],
                score=record["min_score"],
                rank=record["min_rank"],
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
                raw_rows, records = parse_excel_admissions(path, task)
            elif path.suffix.lower() == ".pdf":
                raw_rows, records = parse_pdf_admissions(path, task)
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
    batch = task.get("batch") or "all"
    return f"{province}_{year}_{subject_type}_{batch}"


def main() -> None:
    tasks = load_json(DATA_WORK / "extraction_tasks.json")
    target_tasks = [
        task
        for task in tasks
        if task["document_type"] == DOC_ADMISSIONS
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
        print(f"[admissions] {task['task_id']} -> {len(records)} records")
    print(f"Processed {processed} admissions tasks")


if __name__ == "__main__":
    main()

