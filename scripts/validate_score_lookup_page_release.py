from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from national_extraction_common import ROOT, dump_json, load_json, normalize_text, safe_float, safe_int, write_markdown

APP_ROOT = ROOT / "app"
APP_INDEX = APP_ROOT / "public" / "data" / "score-lookup" / "index.json"
ADMISSIONS_DIR = APP_ROOT / "public" / "data" / "score-lookup" / "admissions"
RANK_DIR = APP_ROOT / "public" / "data" / "score-lookup" / "rank-tables"
AUDIT_JSON = ROOT / "data_work" / "enabled_score_lookup_audit.json"
SIZE_JSON = ROOT / "data_work" / "frontend_data_size_report.json"
VALIDATION_JSON = ROOT / "data_work" / "score_lookup_release_validation.json"
RELEASE_CHECKLIST_MD = ROOT / "docs" / "score_lookup_release_checklist.md"
KNOWN_LIMITS_MD = ROOT / "docs" / "score_lookup_known_limits.md"
SCORE_PAGE = APP_ROOT / "src" / "pages" / "ScoreLookupPage.tsx"
ABOUT_PAGE = APP_ROOT / "src" / "pages" / "AboutPage.tsx"


def resolve_rank(records: list[dict[str, Any]], score: float | None) -> int | None:
    if score is None:
        return None
    exact = next((item for item in records if safe_float(item.get("score")) == score), None)
    if exact is not None:
        return safe_int(exact.get("rank"))
    for item in records:
        item_score = safe_float(item.get("score"))
        if item_score is not None and item_score <= score:
            return safe_int(item.get("rank"))
    return safe_int(records[-1].get("rank")) if records else None


def contains_banned_terms(text: str) -> list[str]:
    banned = ["录取概率", "稳录", "保证录取", "必上", "智能预测录取", "推荐你报考", "一定能上"]
    return [term for term in banned if term in text]


def main() -> None:
    index = load_json(APP_INDEX)
    audit = load_json(AUDIT_JSON)
    size_report = load_json(SIZE_JSON)
    enabled = [item for item in index["datasets"] if item.get("enabled")]
    expected_enabled = sorted(audit["release_keep_dataset_ids"])
    actual_enabled = sorted(item["dataset_id"] for item in enabled)

    admissions_ok = True
    rank_ok = True
    sample_rank_checks = []
    for dataset in enabled:
        admissions_path = APP_ROOT / "public" / Path(dataset["admissions_file"])
        rank_path = APP_ROOT / "public" / Path(dataset["rank_table_file"])
        admissions = load_json(admissions_path)
        ranks = load_json(rank_path)
        if not isinstance(admissions, list) or not admissions:
            admissions_ok = False
        if not isinstance(ranks, list) or not ranks:
            rank_ok = False

        sample_score = safe_float(admissions[min(len(admissions) // 2, len(admissions) - 1)].get("min_score"))
        sample_rank = resolve_rank(ranks, sample_score)
        sample_rank_checks.append(
            {
                "dataset_id": dataset["dataset_id"],
                "sample_score": sample_score,
                "resolved_rank": sample_rank,
                "admissions_records": len(admissions),
                "rank_records": len(ranks),
            }
        )

    source_text = SCORE_PAGE.read_text(encoding="utf-8") + "\n" + ABOUT_PAGE.read_text(encoding="utf-8")
    banned_hits = contains_banned_terms(source_text)
    required_terms = [
        "历史参考",
        "不构成录取承诺",
        "可冲一冲",
        "较为匹配",
        "相对保守",
        "试验版",
    ]
    missing_required = [term for term in required_terms if term not in source_text]

    validation = {
        "enabled_dataset_ids_match_audit": actual_enabled == expected_enabled,
        "enabled_dataset_ids": actual_enabled,
        "admissions_ok": admissions_ok,
        "rank_ok": rank_ok,
        "banned_hits": banned_hits,
        "missing_required_terms": missing_required,
        "frontend_size_mb": round(size_report["after_size_bytes"] / 1024 / 1024, 2),
        "sample_rank_checks": sample_rank_checks,
    }
    dump_json(VALIDATION_JSON, validation)

    checklist_lines = [
        "# Score Lookup Release Checklist",
        "",
        f"- enabled 数据集是否与抽检结论一致：{'是' if validation['enabled_dataset_ids_match_audit'] else '否'}",
        f"- enabled 数据集数量：{len(actual_enabled)}",
        f"- admissions 文件可解析：{'是' if admissions_ok else '否'}",
        f"- rank_table 文件可解析：{'是' if rank_ok else '否'}",
        f"- 前端发布数据体积：{validation['frontend_size_mb']:.2f} MB",
        f"- 是否命中禁用文案：{'否' if not banned_hits else '是'}",
        f"- 是否缺少必要风险提示：{'否' if not missing_required else '是'}",
        "",
        "## Enabled Datasets",
        "",
    ]
    for dataset_id in actual_enabled:
        checklist_lines.append(f"- {dataset_id}")
    checklist_lines.extend(["", "## Rank Conversion Samples", ""])
    for item in sample_rank_checks:
        checklist_lines.append(f"- {json.dumps(item, ensure_ascii=False)}")
    write_markdown(RELEASE_CHECKLIST_MD, "\n".join(checklist_lines))

    limits_lines = [
        "# Score Lookup Known Limits",
        "",
        "- 当前“按分数查志愿（试验版）”只开放少量已通过初步校验的数据集。",
        "- 当前开放范围仅限已通过抽检并完成发布包收敛的数据集。",
        "- 暂不开放大部分候选省份、体育类数据、subject_type=未知 的数据。",
        "- 暂不开放需要 OCR 的数据、人工未复核数据、招生计划数据。",
        "- 结果仅供历史参考，不构成录取承诺。",
        "- 页面不提供录取概率、稳录、保证录取或智能预测录取。",
    ]
    write_markdown(KNOWN_LIMITS_MD, "\n".join(limits_lines))

    print(
        f"validated score-lookup release; enabled={len(actual_enabled)}, "
        f"size={validation['frontend_size_mb']:.2f} MB"
    )


if __name__ == "__main__":
    main()
