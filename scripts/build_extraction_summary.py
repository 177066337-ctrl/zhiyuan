from __future__ import annotations

from collections import Counter
from pathlib import Path

from national_extraction_common import (
    DATA_WORK,
    dump_json,
    iso_now,
    load_json,
    markdown_table,
    summarize_counter,
    write_markdown,
)


def main() -> None:
    tasks = load_json(DATA_WORK / "extraction_tasks.json")
    readiness = load_json(DATA_WORK / "national_validation_reports" / "readiness_summary.json")

    priority_counter = Counter(task["priority"] for task in tasks)
    province_counter = Counter(task["province"] for task in tasks)
    year_counter = Counter(task["year"] for task in tasks)
    subject_counter = Counter(task["subject_type"] for task in tasks)

    extracted_admissions = len(list((DATA_WORK / "national_admissions_normalized").glob("*.normalized.json")))
    extracted_ranks = len(list((DATA_WORK / "national_rank_tables_normalized").glob("*.normalized.json")))
    ready_rows = sorted(
        readiness.values(),
        key=lambda x: (
            not x["ready_for_score_lookup_demo"],
            -x["admissions_records"],
            -x["rank_table_records"],
            x["province"],
        ),
    )
    summary = {
        "generated_at": iso_now(),
        "task_count": len(tasks),
        "priority_counts": dict(priority_counter),
        "extracted_admissions_tasks": extracted_admissions,
        "extracted_rank_tasks": extracted_ranks,
        "ready_rows": ready_rows,
    }
    dump_json(DATA_WORK / "extraction_tasks_summary.json", summary)

    ready_for_demo = [row for row in ready_rows if row["ready_for_score_lookup_demo"]]
    history_only = [row for row in ready_rows if row["has_admissions"] and not row["ready_for_score_lookup_demo"]]
    unusable = [row for row in ready_rows if not row["has_admissions"]]
    top5 = ready_for_demo[:5]

    plan_md = "\n".join(
        [
            "# National Extraction Plan",
            "",
            "1. 本阶段目标：建立全国 admissions 和 rank_table 的批量抽取框架，只处理高可结构化文件。",
            "2. 全国抽取范围：优先 xls/xlsx/csv，其次可提取文本 PDF；需要 OCR 的文件先标记，不混入 normalized。",
            "3. 为什么不直接开发推荐页：当前数据仍存在省份差异、字段缺失和 PDF 结构不稳定问题，直接做推荐会放大误差。",
            "4. admissions 字段结构：year、province、subject_type、batch、school_code、school_name、major_group_code、major_group_name、major_code、major_name、min_score、min_rank、avg_score、max_score、plan_count、admission_count、remarks、source_file、source_sheet/source_page/source_row、extract_method、confidence。",
            "5. rank_table 字段结构：year、province、subject_type、score、same_score_count、cumulative_count、rank、source_file、source_sheet/source_page/source_row、extract_method、confidence。",
            "6. 优先处理规则：文件名元信息完整、结构化表头明确、字段包含最低分/最低位次/累计人数的一律优先。",
            "7. OCR 暂缓规则：图片型、扫描型 PDF、前两页无文本的文件不自动抽取，只进入任务表和报告。",
            "8. 低置信度数据处理规则：保留在 normalized 中，但通过 confidence 和 validation 单列，不直接接入前端正式数据。",
            "9. 后续如何接入前端：只从 ready_for_score_lookup_demo=true 的省份试点，先生成独立试验页数据包。",
        ]
    )
    write_markdown(Path("docs") / "national_extraction_plan.md", plan_md)

    summary_md = "\n".join(
        [
            "# National Extraction Summary",
            "",
            f"- 总任务数: {len(tasks)}",
            f"- high: {priority_counter.get('high', 0)}",
            f"- medium: {priority_counter.get('medium', 0)}",
            f"- low: {priority_counter.get('low', 0)}",
            f"- 已抽取 admissions 任务数: {extracted_admissions}",
            f"- 已抽取 rank_table 任务数: {extracted_ranks}",
            f"- 需要 OCR 的任务数: {sum(1 for task in tasks if task['requires_ocr'])}",
            f"- 需要人工复核的任务数: {sum(1 for task in tasks if task['requires_manual_review'])}",
            "",
            "## 按省份统计",
            markdown_table(summarize_counter(province_counter), ["key", "count"]),
            "",
            "## 按年份统计",
            markdown_table(summarize_counter(year_counter), ["key", "count"]),
            "",
            "## 按科类统计",
            markdown_table(summarize_counter(subject_counter), ["key", "count"]),
            "",
            "## 下一步建议",
            "- 先把 ready 的省份接入试验页，再对 OCR 和人工复核清单逐省补齐。",
        ]
    )
    write_markdown(Path("docs") / "national_extraction_summary.md", summary_md)

    readiness_md = "\n".join(
        [
            "# National Frontend Readiness Report",
            "",
            "## 已具备前端试验条件",
            markdown_table(ready_for_demo, ["province", "year", "subject_type", "admissions_records", "rank_table_records", "ready_reason"]),
            "",
            "## 只适合做历史录取查询",
            markdown_table(history_only[:30], ["province", "year", "subject_type", "admissions_records", "rank_table_records", "blocking_issues"]),
            "",
            "## 暂时不能用",
            markdown_table(unusable[:30], ["province", "year", "subject_type", "admissions_records", "rank_table_records", "blocking_issues"]),
            "",
            "## 建议优先接入的前 5 个试点",
            markdown_table(top5, ["province", "year", "subject_type", "admissions_records", "rank_table_records", "ready_reason"]),
            "",
            f"- 是否建议进入按分数查志愿前端试验页: {'是' if ready_for_demo else '否'}",
        ]
    )
    write_markdown(Path("docs") / "national_frontend_readiness_report.md", readiness_md)
    print(f"Built extraction summary for {len(tasks)} tasks")


if __name__ == "__main__":
    main()
