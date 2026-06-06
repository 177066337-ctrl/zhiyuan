from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from national_extraction_common import (
    DATA_WORK,
    DOC_ADMISSIONS,
    DOC_PLANS,
    DOC_RANK,
    DOC_SUBJECT_REQ,
    DOC_UNKNOWN,
    candidate_text,
    detect_batch,
    detect_province,
    detect_subject_type,
    detect_year,
    dump_json,
    ensure_dir,
    grouped_files_by_task_id,
    iso_now,
    load_json,
    map_document_type,
    priority_from_item,
    selected_from_priority,
    slugify,
    summarize_counter,
    to_lower_ext,
    is_manual_review_needed,
)


def normalize_doc_type(item: dict) -> str:
    text = candidate_text(item)
    mapped = map_document_type(text)
    if mapped != DOC_UNKNOWN:
        return mapped
    if "\u4e00\u5206\u4e00\u6bb5" in text or "\u5206\u6bb5\u7edf\u8ba1" in text:
        return DOC_RANK
    if "\u62db\u751f\u8ba1\u5212" in text:
        return DOC_PLANS
    if "\u9009\u79d1" in text:
        return DOC_SUBJECT_REQ
    if any(key in text for key in ["\u6295\u6863", "\u5f55\u53d6", "\u6700\u4f4e\u5206", "\u5206\u6570\u7ebf"]):
        return DOC_ADMISSIONS
    return DOC_UNKNOWN


def requires_ocr(item: dict) -> bool:
    probe = item.get("probe") or {}
    ext = to_lower_ext(item["file_path"])
    if ext in {".png", ".jpg", ".jpeg"}:
        return True
    return bool(probe.get("needs_ocr"))


def build_tasks() -> tuple[list[dict], dict]:
    resource_items = load_json(DATA_WORK / "resource_inventory.json")
    candidate_items = load_json(DATA_WORK / "admission_candidate_files.json")
    resource_index = {item["file_path"]: item for item in resource_items}

    groups: dict[tuple, list[dict]] = defaultdict(list)
    per_file_meta: dict[str, dict] = {}

    for item in candidate_items:
        base = resource_index.get(item["file_path"], {})
        file_name = item.get("file_name", "")
        file_path = item.get("file_path", "")
        text = candidate_text(item)
        province = detect_province(file_name, "") or detect_province(file_path, base.get("likely_province", ""))
        year = detect_year(file_name, "") or detect_year(file_path, base.get("likely_year", ""))
        subject_type = detect_subject_type(file_name, "") or detect_subject_type(text, base.get("likely_subject_type", ""))
        doc_type = normalize_doc_type(item)
        batch = detect_batch(text)
        ext = to_lower_ext(item["file_path"])
        extractability = (item.get("structured_feasibility") or item.get("extractability") or "\u672a\u77e5")
        priority = priority_from_item(item, doc_type)
        ocr = requires_ocr(item)
        selected, skip_reason = selected_from_priority(priority, ocr)
        manual_review = is_manual_review_needed(item, priority, ocr)

        meta = {
            "province": province,
            "year": year,
            "subject_type": subject_type,
            "batch": batch,
            "document_type": doc_type,
            "file_type": ext.lstrip(".") or "unknown",
            "extractability": extractability,
            "priority": priority,
            "selected": selected,
            "skip_reason": skip_reason,
            "requires_ocr": ocr,
            "requires_manual_review": manual_review,
            "file_path": item["file_path"],
        }
        per_file_meta[item["file_path"]] = meta

        key = (
            province,
            year,
            subject_type,
            batch,
            doc_type,
            meta["file_type"],
            extractability,
        )
        groups[key].append(item)

    tasks: list[dict] = []
    for key, items in sorted(groups.items()):
        province, year, subject_type, batch, doc_type, file_type, extractability = key
        priorities = Counter(per_file_meta[item["file_path"]]["priority"] for item in items)
        task_priority = (
            "high"
            if priorities["high"]
            else "medium"
            if priorities["medium"]
            else "low"
        )
        ocr = any(per_file_meta[item["file_path"]]["requires_ocr"] for item in items)
        manual_review = any(per_file_meta[item["file_path"]]["requires_manual_review"] for item in items)
        selected, skip_reason = selected_from_priority(task_priority, ocr)
        task_id = slugify(doc_type, province, year, subject_type or "unknown", batch or "all", file_type)
        tasks.append(
            {
                "task_id": task_id,
                "province": province,
                "year": year,
                "subject_type": subject_type,
                "batch": batch,
                "document_type": doc_type,
                "candidate_files": sorted(item["file_path"] for item in items),
                "priority": task_priority,
                "extractability": extractability,
                "selected": selected,
                "skip_reason": skip_reason,
                "requires_ocr": ocr,
                "requires_manual_review": manual_review,
                "file_type": file_type,
            }
        )

    summary = {
        "generated_at": iso_now(),
        "task_count": len(tasks),
        "priority_counts": summarize_counter(Counter(task["priority"] for task in tasks)),
        "document_type_counts": summarize_counter(Counter(task["document_type"] for task in tasks)),
        "province_counts": summarize_counter(Counter(task["province"] for task in tasks)),
        "subject_type_counts": summarize_counter(Counter(task["subject_type"] for task in tasks)),
        "requires_ocr_count": sum(1 for task in tasks if task["requires_ocr"]),
        "requires_manual_review_count": sum(1 for task in tasks if task["requires_manual_review"]),
    }
    return tasks, summary


def main() -> None:
    ensure_dir(DATA_WORK)
    tasks, summary = build_tasks()
    dump_json(DATA_WORK / "extraction_tasks.json", tasks)
    dump_json(DATA_WORK / "extraction_tasks_summary.json", summary)
    print(f"Built {len(tasks)} extraction tasks")


if __name__ == "__main__":
    main()
