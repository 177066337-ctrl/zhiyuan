from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from national_extraction_common import PROVINCES, ROOT, dump_json, load_json, normalize_text, safe_int, write_markdown

DATA_WORK = ROOT / "data_work"
APP_BASE = ROOT / "app" / "public" / "data" / "score-lookup"

OUTPUT_JSON = DATA_WORK / "score_lookup_coverage_gaps.json"
OUTPUT_MD = ROOT / "docs" / "score_lookup_coverage_gap_report.md"

VALID_SUBJECTS = {"历史类", "物理类", "文科", "理科", "综合", "体育类"}
UNKNOWN_SUBJECTS = {"", "未知"}


def valid_task_subject(value: str) -> bool:
    return normalize_text(value) in VALID_SUBJECTS


def valid_task_province(value: str) -> bool:
    return normalize_text(value) in PROVINCES


def task_file_signals_subject(task: dict[str, Any], subject_type: str) -> bool:
    keyword = normalize_text(subject_type)
    combined = " ".join(normalize_text(path) for path in task.get("candidate_files", []))
    return keyword and keyword in combined


def compact_task(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_id": task.get("task_id", ""),
        "province": normalize_text(task.get("province")),
        "year": safe_int(task.get("year")),
        "subject_type": normalize_text(task.get("subject_type")),
        "batch": normalize_text(task.get("batch")),
        "document_type": normalize_text(task.get("document_type")),
        "priority": normalize_text(task.get("priority")),
        "requires_ocr": bool(task.get("requires_ocr")),
        "requires_manual_review": bool(task.get("requires_manual_review")),
        "candidate_files": [normalize_text(path) for path in task.get("candidate_files", [])],
    }


def task_matches_dataset(task: dict[str, Any], dataset: dict[str, Any], doc_type: str) -> bool:
    if normalize_text(task.get("document_type")) != doc_type:
        return False
    if normalize_text(task.get("province")) != normalize_text(dataset.get("province")):
        return False
    if safe_int(task.get("year")) != safe_int(dataset.get("year")):
        return False
    task_subject = normalize_text(task.get("subject_type"))
    dataset_subject = normalize_text(dataset.get("subject_type"))
    if task_subject == dataset_subject:
        return True
    if task_subject in UNKNOWN_SUBJECTS and task_file_signals_subject(task, dataset_subject):
        return True
    return False


def summarize_gap_sources(tasks: list[dict[str, Any]]) -> dict[str, int]:
    if not tasks:
        return {"low_priority": 0, "needs_ocr": 0, "needs_manual_review": 0, "no_candidate": 1}
    return {
        "low_priority": sum(1 for task in tasks if normalize_text(task.get("priority")) == "low"),
        "needs_ocr": sum(1 for task in tasks if task.get("requires_ocr")),
        "needs_manual_review": sum(1 for task in tasks if task.get("requires_manual_review")),
        "no_candidate": 0,
    }


def main() -> None:
    resource_inventory = load_json(DATA_WORK / "resource_inventory.json")
    admission_candidates = load_json(DATA_WORK / "admission_candidate_files.json")
    extraction_tasks = [compact_task(task) for task in load_json(DATA_WORK / "extraction_tasks.json")]
    extraction_summary = load_json(DATA_WORK / "extraction_tasks_summary.json")
    index = load_json(APP_BASE / "index.json")
    coverage = load_json(APP_BASE / "coverage.json")

    public_datasets = [dataset for dataset in index["datasets"] if dataset.get("is_public")]
    public_keys = {
        (
            normalize_text(dataset.get("province")),
            safe_int(dataset.get("year")),
            normalize_text(dataset.get("subject_type")),
            normalize_text(dataset.get("batch")),
        )
        for dataset in public_datasets
    }
    current_combo_keys = {
        (
            normalize_text(dataset.get("province")),
            safe_int(dataset.get("year")),
            normalize_text(dataset.get("subject_type")),
        )
        for dataset in public_datasets
    }

    available_years_by_province: dict[str, set[int]] = defaultdict(set)
    available_subjects_by_province: dict[str, set[str]] = defaultdict(set)
    for task in extraction_tasks:
        province = normalize_text(task.get("province"))
        year = safe_int(task.get("year"))
        subject_type = normalize_text(task.get("subject_type"))
        if valid_task_province(province) and year is not None:
            available_years_by_province[province].add(year)
            if valid_task_subject(subject_type):
                available_subjects_by_province[province].add(subject_type)

    open_years_by_province: dict[str, set[int]] = defaultdict(set)
    open_subjects_by_province: dict[str, set[str]] = defaultdict(set)
    for dataset in public_datasets:
        province = normalize_text(dataset.get("province"))
        year = safe_int(dataset.get("year"))
        subject_type = normalize_text(dataset.get("subject_type"))
        if valid_task_province(province) and year is not None:
            open_years_by_province[province].add(year)
            if subject_type not in UNKNOWN_SUBJECTS:
                open_subjects_by_province[province].add(subject_type)

    missing_years_by_province = {
        province: sorted(available_years_by_province[province] - open_years_by_province.get(province, set()))
        for province in sorted(available_years_by_province)
        if available_years_by_province[province] - open_years_by_province.get(province, set())
    }
    missing_subjects_by_province = {
        province: sorted(available_subjects_by_province[province] - open_subjects_by_province.get(province, set()))
        for province in sorted(available_subjects_by_province)
        if available_subjects_by_province[province] - open_subjects_by_province.get(province, set())
    }

    datasets_only_admissions = []
    datasets_only_rank = []
    score_only_datasets = []
    upgradable_by_rank = []
    upgradable_by_admissions = []

    for dataset in public_datasets:
        rank_missing = not normalize_text(dataset.get("rank_table_file"))
        admissions_missing = not normalize_text(dataset.get("admissions_file"))
        if rank_missing and not admissions_missing:
            datasets_only_admissions.append(dataset["dataset_id"])
        if admissions_missing and not rank_missing:
            datasets_only_rank.append(dataset["dataset_id"])
        if normalize_text(dataset.get("quality_status")) == "score_only":
            score_only_datasets.append(dataset["dataset_id"])

        rank_tasks = [
            task
            for task in extraction_tasks
            if task_matches_dataset(task, dataset, "rank_table")
        ]
        if rank_missing and rank_tasks:
            upgradable_by_rank.append(
                {
                    "dataset_id": dataset["dataset_id"],
                    "province": dataset["province"],
                    "year": dataset["year"],
                    "subject_type": dataset["subject_type"],
                    "task_ids": [task["task_id"] for task in rank_tasks],
                    "gap_sources": summarize_gap_sources(rank_tasks),
                }
            )

    existing_admission_keys = {
        (
            normalize_text(dataset.get("province")),
            safe_int(dataset.get("year")),
            normalize_text(dataset.get("subject_type")),
            normalize_text(dataset.get("batch")),
        )
        for dataset in public_datasets
    }

    for task in extraction_tasks:
        if normalize_text(task.get("document_type")) != "admissions":
            continue
        province = normalize_text(task.get("province"))
        year = safe_int(task.get("year"))
        subject_type = normalize_text(task.get("subject_type"))
        batch = normalize_text(task.get("batch"))
        if not valid_task_province(province) or year is None or not valid_task_subject(subject_type):
            continue
        key = (province, year, subject_type, batch)
        if key in existing_admission_keys:
            continue
        upgradable_by_admissions.append(
            {
                "province": province,
                "year": year,
                "subject_type": subject_type,
                "batch": batch,
                "task_id": task["task_id"],
                "priority": task["priority"],
                "requires_ocr": task["requires_ocr"],
                "requires_manual_review": task["requires_manual_review"],
                "candidate_files": task["candidate_files"][:5],
            }
        )

    gap_sources = Counter()
    for item in upgradable_by_rank:
        for key, value in item["gap_sources"].items():
            gap_sources[key] += value

    tasks_by_status = {
        "low_priority": [
            task["task_id"] for task in extraction_tasks if task["priority"] == "low"
        ],
        "needs_ocr": [
            task["task_id"] for task in extraction_tasks if task["requires_ocr"]
        ],
        "needs_manual_review": [
            task["task_id"] for task in extraction_tasks if task["requires_manual_review"]
        ],
    }

    payload = {
        "open_dataset_count": len(public_datasets),
        "open_province_count": len({dataset["province"] for dataset in public_datasets}),
        "open_year_count": len({dataset["year"] for dataset in public_datasets}),
        "open_subject_count": len({dataset["subject_type"] for dataset in public_datasets}),
        "open_years_by_province": {
            province: sorted(years) for province, years in sorted(open_years_by_province.items())
        },
        "missing_years_by_province": missing_years_by_province,
        "missing_subjects_by_province": missing_subjects_by_province,
        "datasets_only_admissions": datasets_only_admissions,
        "datasets_only_rank_table": datasets_only_rank,
        "score_only_datasets": score_only_datasets,
        "upgradable_by_rank": upgradable_by_rank,
        "upgradable_by_admissions": upgradable_by_admissions,
        "gap_sources": dict(gap_sources),
        "coverage_rows": len(coverage.get("rows", [])),
        "resource_inventory_count": len(resource_inventory) if isinstance(resource_inventory, list) else 0,
        "admission_candidate_count": len(admission_candidates) if isinstance(admission_candidates, list) else 0,
        "tasks_summary": extraction_summary,
        "tasks_by_status": tasks_by_status,
        "current_combo_count": len(current_combo_keys),
        "current_combo_keys": [
            {"province": province, "year": year, "subject_type": subject_type}
            for province, year, subject_type in sorted(current_combo_keys)
        ],
    }
    dump_json(OUTPUT_JSON, payload)

    lines = [
        "# Score Lookup Coverage Gap Report",
        "",
        f"- 当前前端已开放数据集数量：{payload['open_dataset_count']}",
        f"- 当前前端已开放省份数量：{payload['open_province_count']}",
        f"- 当前前端已开放年份数量：{payload['open_year_count']}",
        f"- 当前前端已开放科类数量：{payload['open_subject_count']}",
        f"- 当前 coverage 行数：{payload['coverage_rows']}",
        "",
        "## 主要缺口",
        "",
        f"- 只有 admissions、没有 rank_table 的数据集：{len(datasets_only_admissions)}",
        f"- 只有 rank_table、没有 admissions 的数据集：{len(datasets_only_rank)}",
        f"- 当前 score_only 数据集：{len(score_only_datasets)}",
        f"- 通过补 rank_table 有机会升级的数据集：{len(upgradable_by_rank)}",
        f"- 通过补 admissions 有机会补进前端的数据集：{len(upgradable_by_admissions)}",
        "",
        "## 缺口来源统计",
        "",
        f"- low priority：{gap_sources.get('low_priority', 0)}",
        f"- needs_ocr：{gap_sources.get('needs_ocr', 0)}",
        f"- needs_manual_review：{gap_sources.get('needs_manual_review', 0)}",
        f"- 暂无候选任务：{gap_sources.get('no_candidate', 0)}",
        "",
        "## 省份年份缺口",
        "",
    ]

    for province in sorted(missing_years_by_province):
        lines.append(f"- {province} 缺失年份：{', '.join(str(year) for year in missing_years_by_province[province])}")

    lines.extend(["", "## 省份科类缺口", ""])
    for province in sorted(missing_subjects_by_province):
        lines.append(f"- {province} 缺失科类：{', '.join(missing_subjects_by_province[province])}")

    lines.extend(["", "## 优先补全建议", ""])
    top_rank = upgradable_by_rank[:20]
    if top_rank:
        for item in top_rank:
            lines.append(
                f"- {item['province']} {item['year']} {item['subject_type']}：可优先尝试补 rank_table，关联任务 {', '.join(item['task_ids'][:3])}"
            )
    else:
        lines.append("- 当前没有可直接命中的 rank_table 补全任务。")

    write_markdown(OUTPUT_MD, "\n".join(lines))
    print(
        f"analyzed score lookup gaps: datasets={payload['open_dataset_count']}, "
        f"score_only={len(score_only_datasets)}, rank_upgradable={len(upgradable_by_rank)}"
    )


if __name__ == "__main__":
    main()
