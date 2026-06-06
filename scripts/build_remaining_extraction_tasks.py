from __future__ import annotations

from pathlib import Path

from national_extraction_common import DATA_WORK, dump_json, ensure_dir, is_pdf_text_extractable, load_json, write_markdown
from remaining_extraction_support import PROGRESS_PATH, FAILURES_PATH, init_progress, task_output_name


def national_output_exists(task: dict) -> bool:
    name = task_output_name(task)
    if task["document_type"] == "admissions":
        path = DATA_WORK / "national_admissions_normalized" / name
        return path.exists()
    if task["document_type"] == "rank_table":
        path = DATA_WORK / "national_rank_tables_normalized" / name
        return path.exists()
    return False


def build_tasks() -> list[dict]:
    tasks = load_json(DATA_WORK / "extraction_tasks.json")
    remaining = []
    for task in tasks:
        doc_type = task["document_type"]
        include = False
        if task["priority"] == "low":
            include = True
        if task["requires_ocr"]:
            include = True
        if doc_type in {"plans", "subject_requirement"}:
            include = True
        if doc_type in {"admissions", "rank_table"} and not national_output_exists(task):
            include = True
        if not include:
            continue

        planned_action = "probe_ocr" if task["requires_ocr"] else "extract"
        risk_level = "high" if task["requires_ocr"] else "medium" if task["priority"] == "low" else "low"
        output_file = ""
        if planned_action == "extract":
            output_file = task_output_name(task)
        remaining.append(
            {
                "task_id": task["task_id"],
                "province": task.get("province", ""),
                "year": task.get("year"),
                "subject_type": task.get("subject_type", ""),
                "batch": task.get("batch", ""),
                "document_type": doc_type,
                "priority": task.get("priority", ""),
                "requires_ocr": task.get("requires_ocr", False),
                "candidate_files": task.get("candidate_files", []),
                "planned_action": planned_action,
                "status": "pending",
                "output_file": output_file,
                "skip_reason": "",
                "risk_level": risk_level,
            }
        )
    return remaining


def main() -> None:
    ensure_dir(DATA_WORK)
    remaining = build_tasks()
    dump_json(DATA_WORK / "remaining_extraction_tasks.json", remaining)
    if PROGRESS_PATH.exists():
        PROGRESS_PATH.unlink()
    if FAILURES_PATH.exists():
        FAILURES_PATH.unlink()
    init_progress(remaining)
    plan = "\n".join(
        [
            "# Remaining Extraction Plan",
            "",
            f"- 剩余任务总数: {len(remaining)}",
            "- 只处理尚未完成或未纳入一期自动抽取范围的任务。",
            "- 已存在且 JSON 可解析的输出默认跳过。",
            "- OCR 任务本阶段只做样本探测，不做全量识别。",
            "- low 优先级 admissions / rank_table 进入独立 remaining 输出目录，不回写 national_*。",
            "- 每个任务记录状态并定期写进度报告。",
        ]
    )
    write_markdown(Path("docs") / "remaining_extraction_plan.md", plan)
    print(f"Built {len(remaining)} remaining tasks")


if __name__ == "__main__":
    main()

