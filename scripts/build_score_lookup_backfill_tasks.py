from __future__ import annotations

from pathlib import Path
from typing import Any

from national_extraction_common import DATA_WORK, dump_json, load_json, normalize_text, safe_int

OUTPUT_PATH = DATA_WORK / "score_lookup_backfill_tasks.json"


def rank_task_priority(task: dict[str, Any], desired_subject: str) -> str:
    if task.get("requires_ocr"):
        return "low"
    if task.get("requires_manual_review"):
        return "low"
    task_subject = normalize_text(task.get("subject_type"))
    if task_subject == normalize_text(desired_subject):
        return "high"
    if task_subject in {"", "未知"}:
        return "medium"
    return normalize_text(task.get("priority")) or "low"


def planned_action(task: dict[str, Any], missing_type: str) -> str:
    if task.get("requires_ocr"):
        return "probe_ocr"
    if task.get("requires_manual_review"):
        return "manual_review"
    if missing_type == "rank_table":
        return "extract_rank_table"
    if missing_type in {"admissions", "both"}:
        return "extract_admissions"
    return "skip"


def main() -> None:
    gaps = load_json(DATA_WORK / "score_lookup_coverage_gaps.json")
    tasks = load_json(DATA_WORK / "extraction_tasks.json")

    rank_tasks = [task for task in tasks if normalize_text(task.get("document_type")) == "rank_table"]
    admissions_tasks = [task for task in tasks if normalize_text(task.get("document_type")) == "admissions"]

    output: list[dict[str, Any]] = []

    public_dataset_lookup = {
        dataset["dataset_id"]: dataset
        for dataset in load_json(Path("app/public/data/score-lookup/index.json"))["datasets"]
    }

    for dataset_id in gaps.get("score_only_datasets", []):
        dataset = public_dataset_lookup.get(dataset_id)
        if not dataset:
            continue
        matches = [
            task
            for task in rank_tasks
            if normalize_text(task.get("province")) == normalize_text(dataset.get("province"))
            and safe_int(task.get("year")) == safe_int(dataset.get("year"))
            and (
                normalize_text(task.get("subject_type")) == normalize_text(dataset.get("subject_type"))
                or normalize_text(task.get("subject_type")) in {"", "未知"}
            )
        ]
        if not matches:
            output.append(
                {
                    "task_id": f"backfill_rank_missing__{dataset_id}",
                    "province": dataset.get("province", ""),
                    "year": dataset.get("year"),
                    "subject_type": dataset.get("subject_type", ""),
                    "batch": dataset.get("batch", ""),
                    "missing_type": "rank_table",
                    "current_status": dataset.get("quality_status", "score_only"),
                    "candidate_source_files": [],
                    "source_task_ids": [],
                    "priority": "low",
                    "requires_ocr": False,
                    "requires_manual_review": False,
                    "planned_action": "skip",
                    "reason": "未找到同省份同年份的 rank_table 候选任务",
                }
            )
            continue

        requires_ocr = any(task.get("requires_ocr") for task in matches)
        requires_manual_review = any(task.get("requires_manual_review") for task in matches)
        priority = "low"
        if any(rank_task_priority(task, dataset.get("subject_type", "")) == "high" for task in matches):
            priority = "high"
        elif any(rank_task_priority(task, dataset.get("subject_type", "")) == "medium" for task in matches):
            priority = "medium"

        output.append(
            {
                "task_id": f"backfill_rank__{dataset_id}",
                "province": dataset.get("province", ""),
                "year": dataset.get("year"),
                "subject_type": dataset.get("subject_type", ""),
                "batch": dataset.get("batch", ""),
                "missing_type": "rank_table",
                "current_status": dataset.get("quality_status", "score_only"),
                "candidate_source_files": [
                    path
                    for task in matches
                    for path in task.get("candidate_files", [])
                ],
                "source_task_ids": [task.get("task_id", "") for task in matches],
                "priority": priority,
                "requires_ocr": requires_ocr,
                "requires_manual_review": requires_manual_review,
                "planned_action": planned_action(matches[0], "rank_table"),
                "reason": "当前数据集缺少可靠 rank_table，可尝试按同省份同年份候选任务补全",
            }
        )

    existing_frontend_keys = {
        (
            normalize_text(dataset.get("province")),
            safe_int(dataset.get("year")),
            normalize_text(dataset.get("subject_type")),
            normalize_text(dataset.get("batch")),
        )
        for dataset in public_dataset_lookup.values()
        if dataset.get("is_public")
    }

    for task in admissions_tasks:
        province = normalize_text(task.get("province"))
        year = safe_int(task.get("year"))
        subject_type = normalize_text(task.get("subject_type"))
        batch = normalize_text(task.get("batch"))
        if province in {"", "未知"} or year is None or subject_type in {"", "未知"}:
            continue
        key = (province, year, subject_type, batch)
        if key in existing_frontend_keys:
            continue

        output.append(
            {
                "task_id": f"backfill_admissions__{task.get('task_id', '')}",
                "province": province,
                "year": year,
                "subject_type": subject_type,
                "batch": batch,
                "missing_type": "admissions",
                "current_status": "missing",
                "candidate_source_files": task.get("candidate_files", []),
                "source_task_ids": [task.get("task_id", "")],
                "priority": normalize_text(task.get("priority")) or "low",
                "requires_ocr": bool(task.get("requires_ocr")),
                "requires_manual_review": bool(task.get("requires_manual_review")),
                "planned_action": planned_action(task, "admissions"),
                "reason": "当前前端未开放该 admissions 组合，可作为候选补入前端层",
            }
        )

    output.sort(
        key=lambda item: (
            {"high": 0, "medium": 1, "low": 2}.get(item["priority"], 9),
            item["missing_type"],
            item["province"],
            item["year"] or 9999,
            item["subject_type"],
            item["batch"],
        )
    )

    dump_json(OUTPUT_PATH, output)
    print(f"built {len(output)} score lookup backfill tasks")


if __name__ == "__main__":
    main()
