from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from national_extraction_common import DATA_WORK, dump_json, extract_pdf_text, load_json, normalize_text, to_lower_ext, write_markdown

OUTPUT_JSON = DATA_WORK / "score_lookup_ocr_backfill_candidates.json"
OUTPUT_MD = DATA_WORK.parent / "docs" / "score_lookup_ocr_backfill_report.md"


def ocr_priority(task: dict[str, Any]) -> str:
    if task.get("missing_type") == "rank_table":
        return "high"
    if task.get("missing_type") == "admissions":
        return "medium"
    return "low"


def probe_file(path_text: str) -> dict[str, Any]:
    path = Path(path_text)
    payload = {
        "file_path": str(path),
        "extension": path.suffix.lower(),
        "size_mb": round(path.stat().st_size / 1024 / 1024, 2) if path.exists() else 0,
        "samples": [],
        "likely_readable": False,
    }
    if not path.exists() or to_lower_ext(str(path)) != ".pdf":
        return payload
    try:
        pages = extract_pdf_text(path, max_pages=3)
        for page in pages[:3]:
            text = normalize_text(page.get("text"))[:200]
            payload["samples"].append({"page": page.get("page"), "text_preview": text})
        payload["likely_readable"] = any(sample["text_preview"] for sample in payload["samples"])
    except Exception as exc:
        payload["error"] = str(exc)
    return payload


def main() -> None:
    tasks = load_json(DATA_WORK / "score_lookup_backfill_tasks.json")
    targets = [task for task in tasks if task.get("requires_ocr")]
    rows = []
    counts = Counter()
    for task in targets:
        priority = ocr_priority(task)
        counts[priority] += 1
        rows.append(
            {
                "task_id": task["task_id"],
                "province": task.get("province", ""),
                "year": task.get("year"),
                "subject_type": task.get("subject_type", ""),
                "batch": task.get("batch", ""),
                "missing_type": task.get("missing_type", ""),
                "ocr_priority": priority,
                "candidate_files": task.get("candidate_source_files", []),
                "probes": [probe_file(path) for path in task.get("candidate_source_files", [])[:3]],
            }
        )
    dump_json(OUTPUT_JSON, rows)
    lines = [
        "# Score Lookup OCR Backfill Report",
        "",
        f"- 需要 OCR 的缺口任务数：{len(rows)}",
        f"- high：{counts['high']}",
        f"- medium：{counts['medium']}",
        f"- low：{counts['low']}",
        "",
        "- 本阶段只做 1-3 页样本探测，不做全量 OCR。",
        "- rank_table 缺口优先级最高，其次是 admissions。",
        "- 无法稳定提取文本的 PDF 不直接进入前端候选层。",
    ]
    write_markdown(OUTPUT_MD, "\n".join(lines))
    print(f"probed {len(rows)} OCR backfill candidates")


if __name__ == "__main__":
    main()
