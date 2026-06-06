from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from national_extraction_common import completion_rate, dump_json, load_json, normalize_text, write_markdown
from remaining_extraction_support import (
    FAILURES_PATH,
    PLANS_NORMALIZED,
    PROGRESS_PATH,
    REMAINING_ADMISSIONS_NORMALIZED,
    REMAINING_RANK_NORMALIZED,
    SUBJECT_NORMALIZED,
)


def load_records(dir_path: Path) -> tuple[int, int, int, float]:
    file_count = 0
    record_count = 0
    json_errors = 0
    low_conf_count = 0
    for path in dir_path.glob("*.json"):
        file_count += 1
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            json_errors += 1
            continue
        if isinstance(data, list):
            record_count += len(data)
            low_conf_count += sum(1 for row in data if normalize_text(row.get("confidence")) == "low")
    low_ratio = low_conf_count / max(record_count, 1)
    return file_count, record_count, json_errors, low_ratio


def main() -> None:
    admissions_files, admissions_records, admissions_json_errors, admissions_low_ratio = load_records(REMAINING_ADMISSIONS_NORMALIZED)
    rank_files, rank_records, rank_json_errors, rank_low_ratio = load_records(REMAINING_RANK_NORMALIZED)
    plans_files, plans_records, plans_json_errors, plans_low_ratio = load_records(PLANS_NORMALIZED)
    subject_files, subject_records, subject_json_errors, subject_low_ratio = load_records(SUBJECT_NORMALIZED)

    progress = load_json(PROGRESS_PATH)
    failures = load_json(FAILURES_PATH) if FAILURES_PATH.exists() else []
    status_counter = Counter(task["status"] for task in progress["tasks"])
    doc_counter = Counter(task["document_type"] for task in progress["tasks"])
    ocr_probe_count = len(load_json(Path("data_work") / "ocr_required_probe_results.json")) if (Path("data_work") / "ocr_required_probe_results.json").exists() else 0

    lines = [
        "# Remaining Extraction Validation Report",
        "",
        f"- remaining admissions 文件数: {admissions_files}",
        f"- remaining admissions 记录数: {admissions_records}",
        f"- remaining rank_table 文件数: {rank_files}",
        f"- remaining rank_table 记录数: {rank_records}",
        f"- plans 文件数: {plans_files}",
        f"- plans 记录数: {plans_records}",
        f"- subject_requirement 文件数: {subject_files}",
        f"- subject_requirement 记录数: {subject_records}",
        f"- OCR probe 文件数: {ocr_probe_count}",
        f"- JSON 解析错误数量: {admissions_json_errors + rank_json_errors + plans_json_errors + subject_json_errors}",
        f"- 低置信度比例 admissions: {admissions_low_ratio:.2%}",
        f"- 低置信度比例 rank_table: {rank_low_ratio:.2%}",
        f"- 低置信度比例 plans: {plans_low_ratio:.2%}",
        f"- 低置信度比例 subject_requirement: {subject_low_ratio:.2%}",
        f"- failed 数量: {status_counter.get('failed', 0)}",
        f"- timeout 数量: {status_counter.get('timeout', 0)}",
        f"- needs_manual_review 数量: {status_counter.get('needs_manual_review', 0)}",
        "",
        "## 按 document_type 统计",
    ]
    for key, value in sorted(doc_counter.items()):
        lines.append(f"- {key}: {value}")
    lines += ["", "## Failed / Timeout Tasks"]
    if failures:
        for item in failures[:100]:
            lines.append(f"- {item['task_id']}: {item['status']} - {item.get('notes', '')}")
    else:
        lines.append("- None")
    write_markdown(Path("docs") / "remaining_extraction_validation_report.md", "\n".join(lines))

    plans_lines = [
        "# Plans Extraction Report",
        "",
        f"- plans 任务数: {doc_counter.get('plans', 0)}",
        f"- 成功抽取数量: {status_counter.get('completed', 0) + status_counter.get('needs_manual_review', 0)}",
        f"- plans normalized 总记录数: {plans_records}",
        "- plan_count 完整率: 待后续字段级专项校验",
        "- 主要字段缺失情况: tuition / duration / degree_level / subject_requirement 依赖原文件表头，完整度不稳定。",
        "- 是否适合后续接入前端: 暂不建议直接接入，需先做字段标准化和人工复核。",
    ]
    write_markdown(Path("docs") / "plans_extraction_report.md", "\n".join(plans_lines))

    subject_lines = [
        "# Subject Requirements Extraction Report",
        "",
        f"- subject_requirement 任务数: {doc_counter.get('subject_requirement', 0)}",
        f"- 成功抽取数量: {status_counter.get('completed', 0) + status_counter.get('needs_manual_review', 0)}",
        f"- normalized 总记录数: {subject_records}",
        "- subject_requirement 完整率: 待后续字段级专项校验",
        "- 缺失情况: 说明型 PDF 和泛政策文件较多，可结构化样本有限。",
        "- 是否适合补充专业页或计划页: 可以作为后续补充方向，但还不适合直接合并到正式前端数据。",
    ]
    write_markdown(Path("docs") / "subject_requirements_extraction_report.md", "\n".join(subject_lines))
    print("Remaining extraction validation complete")


if __name__ == "__main__":
    main()
