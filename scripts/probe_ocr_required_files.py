from __future__ import annotations

from collections import Counter
from pathlib import Path

import pdfplumber

from national_extraction_common import DATA_WORK, dump_json, normalize_text, write_markdown
from remaining_extraction_support import load_remaining_tasks, update_task_status, write_progress_markdown


def probe_pdf(path: Path) -> dict:
    with pdfplumber.open(path) as pdf:
        page_count = len(pdf.pages)
        probe_pages = sorted({1, max(1, page_count // 2), page_count})
        samples = []
        for page_no in probe_pages:
            page = pdf.pages[page_no - 1]
            text = normalize_text(page.extract_text() or "")
            samples.append({"page": page_no, "text_length": len(text), "preview": text[:200]})
    return {"page_count": page_count, "samples": samples}


def main() -> None:
    tasks = [task for task in load_remaining_tasks() if task["requires_ocr"]]
    results = []
    for task in tasks:
        file_path = Path(task["candidate_files"][0]) if task["candidate_files"] else None
        result = {
            "task_id": task["task_id"],
            "province": task.get("province", ""),
            "year": task.get("year"),
            "subject_type": task.get("subject_type", ""),
            "document_type": task.get("document_type", ""),
            "file_path": str(file_path) if file_path else "",
            "file_type": file_path.suffix.lower() if file_path else "",
            "size_mb": round(file_path.stat().st_size / (1024 * 1024), 3) if file_path and file_path.exists() else None,
            "ocr_priority": "low",
            "readability": "unknown",
            "notes": "",
        }
        try:
            if file_path and file_path.suffix.lower() == ".pdf":
                probe = probe_pdf(file_path)
                result.update(probe)
                text_lengths = [sample["text_length"] for sample in probe["samples"]]
                if max(text_lengths or [0]) > 200:
                    result["readability"] = "partially_extractable"
                else:
                    result["readability"] = "ocr_needed"
            else:
                result["readability"] = "ocr_needed"
        except Exception as exc:
            result["notes"] = str(exc)
            result["readability"] = "probe_failed"

        if task["document_type"] in {"admissions", "rank_table"}:
            result["ocr_priority"] = "high"
        elif task["document_type"] in {"plans", "subject_requirement"}:
            result["ocr_priority"] = "medium"
        else:
            result["ocr_priority"] = "low"
        results.append(result)
        update_task_status(task["task_id"], "needs_ocr", notes=result["readability"], output_file=result["file_path"])
    dump_json(DATA_WORK / "ocr_required_probe_results.json", results)

    doc_counter = Counter(item["document_type"] for item in results)
    province_counter = Counter(item["province"] for item in results)
    priority_counter = Counter(item["ocr_priority"] for item in results)
    lines = [
        "# OCR Required Files Report",
        "",
        f"- 需要 OCR 的任务数: {len(results)}",
        "## 按 document_type 分布",
    ]
    for key, value in sorted(doc_counter.items()):
        lines.append(f"- {key}: {value}")
    lines += ["", "## 按省份分布"]
    for key, value in province_counter.most_common(30):
        lines.append(f"- {key}: {value}")
    lines += ["", "## OCR 优先级"]
    for key, value in sorted(priority_counter.items()):
        lines.append(f"- {key}: {value}")
    lines += [
        "",
        "- 是否建议后续单独做 OCR 阶段: 是",
        "- 不建议全量 OCR 的原因: 文件量大、重复资料多、扫描质量不稳定、成本高且低价值说明性文件占比不低。",
    ]
    write_markdown(Path("docs") / "ocr_required_files_report.md", "\n".join(lines))
    write_progress_markdown()
    print(f"Probed {len(results)} OCR-required tasks")


if __name__ == "__main__":
    main()

