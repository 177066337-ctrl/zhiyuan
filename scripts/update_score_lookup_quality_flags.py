from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from national_extraction_common import (
    PROVINCES,
    ROOT,
    dump_json,
    iso_now,
    load_json,
    normalize_text,
    safe_int,
    write_markdown,
)

APP_BASE = ROOT / "app" / "public" / "data" / "score-lookup"
INDEX_PATH = APP_BASE / "index.json"
COVERAGE_PATH = APP_BASE / "coverage.json"
RELEASE_REPORT = ROOT / "docs" / "national_candidate_release_report.md"
KNOWN_LIMITS = ROOT / "docs" / "score_lookup_known_limits.md"

VERIFIED_IDS = {
    "福建_2023_历史类_本科批",
    "福建_2023_历史类_专科批",
}

WARNING_IDS = {
    "江西_2025_历史类_本科",
    "江西_2025_历史类_专科",
    "江西_2025_历史类_征集志愿",
}

STATUS_PRIORITY = {
    "verified": 0,
    "candidate": 1,
    "warning": 2,
    "score_only": 3,
    "unavailable": 4,
}

STATUS_TO_COVERAGE = {
    "verified": "open_verified",
    "candidate": "open_candidate",
    "warning": "open_warning",
    "score_only": "score_only",
    "unavailable": "unavailable",
}


def file_exists(path_text: str) -> bool:
    return (ROOT / "app" / "public" / path_text).exists()


def public_sort_key(item: dict[str, Any]) -> tuple[Any, ...]:
    return (
        STATUS_PRIORITY.get(item["quality_status"], 9),
        item["province"] not in PROVINCES,
        item["province"],
        item["year"],
        item["subject_type"],
        item["batch"],
    )


def classify_dataset(dataset: dict[str, Any]) -> tuple[str, str, str, bool, bool]:
    dataset_id = dataset["dataset_id"]
    admissions_ok = file_exists(dataset["admissions_file"])
    rank_ok = bool(dataset.get("rank_table_file")) and file_exists(dataset["rank_table_file"])
    admissions_records = safe_int(dataset.get("admissions_records")) or 0
    min_score_rate = float(dataset.get("min_score_complete_rate") or 0)
    min_rank_rate = float(dataset.get("min_rank_complete_rate") or 0)
    rank_records = safe_int(dataset.get("rank_table_records")) or 0
    score_rate = float(dataset.get("score_complete_rate") or 0)
    rank_rate = float(dataset.get("rank_complete_rate") or 0)

    if dataset_id in VERIFIED_IDS:
        return (
            "verified",
            "已抽检通过",
            "该数据集已通过初步抽检，但仍不构成录取承诺。",
            True,
            False,
        )

    if dataset_id in WARNING_IDS:
        return (
            "warning",
            "抽检有问题",
            "该数据集抽检发现问题，开放仅用于资料查看，不建议直接作为填报依据。",
            True,
            True,
        )

    if not admissions_ok or admissions_records < 1:
        return (
            "unavailable",
            "暂不可用",
            "当前数据文件不完整，不进入普通查询。",
            False,
            False,
        )

    if (
        rank_ok
        and rank_records >= 100
        and score_rate >= 0.95
        and rank_rate >= 0.95
        and min_score_rate >= 0.80
        and min_rank_rate >= 0.70
    ):
        return (
            "candidate",
            "未人工复核",
            "该数据集尚未人工复核，仅供历史数据参考。",
            True,
            True,
        )

    return (
        "score_only",
        "仅分数参考",
        "该数据集缺少可靠位次支撑，只能查询历史最低分参考。",
        True,
        True,
    )


def build_coverage(datasets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, int, str], list[dict[str, Any]]] = defaultdict(list)
    for dataset in datasets:
        key = (dataset["province"], int(dataset["year"]), dataset["subject_type"])
        grouped[key].append(dataset)

    coverage_rows = []
    for (province, year, subject_type), rows in sorted(grouped.items()):
        public_rows = [row for row in rows if row["is_public"]]
        chosen = sorted(public_rows or rows, key=public_sort_key)[0]
        coverage_rows.append(
            {
                "province": province,
                "year": year,
                "subject_type": subject_type,
                "status": STATUS_TO_COVERAGE[chosen["quality_status"]],
                "label": chosen["quality_label"],
                "notice": chosen["quality_notice"],
                "batches": [row["batch"] for row in sorted(rows, key=lambda item: item["batch"])],
                "public_batches": [
                    row["batch"] for row in sorted(public_rows, key=lambda item: item["batch"])
                ],
            }
        )
    return coverage_rows


def main() -> None:
    index = load_json(INDEX_PATH)

    updated_datasets = []
    for dataset in index["datasets"]:
        quality_status, quality_label, quality_notice, is_public, requires_warning = classify_dataset(dataset)
        item = dict(dataset)
        item["notes"] = normalize_text(item.get("notes")).replace("release_hidden", "").strip("; ").strip()
        item["quality_status"] = quality_status
        item["quality_label"] = quality_label
        item["quality_notice"] = quality_notice
        item["is_public"] = is_public
        item["requires_warning"] = requires_warning
        item["enabled"] = is_public
        updated_datasets.append(item)

    updated_datasets.sort(key=public_sort_key)
    index["generated_at"] = iso_now()
    index["version"] = "score_lookup_candidate_release_v1"
    index["notice"] = (
        "本数据仅供历史参考，不构成录取承诺。部分数据尚未人工复核，请谨慎查看。"
    )
    index["datasets"] = updated_datasets
    dump_json(INDEX_PATH, index)

    coverage = {
        "generated_at": iso_now(),
        "notice": "全国候选数据试验版覆盖状态，仅反映当前前端可选数据，不代表完整或最终质量。",
        "rows": build_coverage(updated_datasets),
    }
    dump_json(COVERAGE_PATH, coverage)

    counts = Counter(item["quality_status"] for item in updated_datasets)
    score_lookup_size = sum(path.stat().st_size for path in APP_BASE.rglob("*.json"))
    admissions_sizes = sorted(
        ((path.name, path.stat().st_size) for path in (APP_BASE / "admissions").glob("*.json")),
        key=lambda item: item[1],
        reverse=True,
    )
    max_adm_name, max_adm_size = admissions_sizes[0] if admissions_sizes else ("", 0)

    lines = [
        "# National Candidate Release Report",
        "",
        f"- 开放数据集总数：{len(updated_datasets)}",
        f"- verified 数量：{counts['verified']}",
        f"- warning 数量：{counts['warning']}",
        f"- candidate 数量：{counts['candidate']}",
        f"- score_only 数量：{counts['score_only']}",
        f"- unavailable 数量：{counts['unavailable']}",
        f"- 前端数据总体积：{score_lookup_size / 1024 / 1024:.2f} MB",
        f"- 最大单个 admissions 分片：{max_adm_name} ({max_adm_size / 1024 / 1024:.2f} MB)",
        "",
        "## 需要谨慎的数据",
        "",
        "- 江西 2025 历史类：开放试查，抽检发现问题，请谨慎参考。",
        "- 其他 candidate 数据集：尚未人工复核，仅供历史数据参考。",
        "- score_only 数据集：只支持历史最低分查询，不支持可靠的分数换位次。",
        "",
        "## 仍未开放的数据",
        "",
        "- needs_ocr 原始文件",
        "- failed 任务结果",
        "- 16G 原始资料",
        "- data_work 原始大 JSON 全集",
        "- plans_normalized 全量文件",
        "- subject_requirements_normalized",
        "",
        "## 为什么这是试验版",
        "",
        "- 全国候选数据来源复杂，质量并不一致。",
        "- 目前只对少量数据集做过人工抽检。",
        "- 部分数据缺少可靠 rank table 或存在字段错位风险。",
        "- 页面只提供历史参考，不提供录取概率或正式推荐。",
    ]
    write_markdown(RELEASE_REPORT, "\n".join(lines))

    limits_lines = [
        "# Score Lookup Known Limits",
        "",
        "- 当前“按分数查志愿（全国候选试验版）”会展示全国候选数据，但质量并不一致。",
        "- 福建 2023 历史类已完成初步抽检；江西 2025 历史类为警示数据；其余多数候选数据仍未人工复核。",
        "- 部分数据只支持历史最低分查询，不支持可靠的分数换位次。",
        "- 本工具不是正式志愿推荐系统，不提供录取概率。",
        "- 需要 OCR 的资料、failed 结果、招生计划数据和选科要求数据暂未对前端开放。",
        "- 结果仅供资料查看和历史参考，不构成录取承诺。",
    ]
    write_markdown(KNOWN_LIMITS, "\n".join(limits_lines))

    print(
        f"updated quality flags for {len(updated_datasets)} datasets: "
        f"verified={counts['verified']}, warning={counts['warning']}, "
        f"candidate={counts['candidate']}, score_only={counts['score_only']}"
    )


if __name__ == "__main__":
    main()
