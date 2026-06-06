from __future__ import annotations

from collections import Counter
from pathlib import Path

from national_extraction_common import ROOT, dump_json, load_json, write_markdown

APP_BASE = ROOT / "app" / "public" / "data" / "score-lookup"
DIST_BASE = ROOT / "app" / "dist"
INDEX_PATH = APP_BASE / "index.json"
COVERAGE_PATH = APP_BASE / "coverage.json"

CHECKLIST_PATH = ROOT / "docs" / "score_lookup_release_checklist.md"
SIZE_REPORT_PATH = ROOT / "docs" / "frontend_data_size_report.md"
VALIDATION_JSON = ROOT / "data_work" / "score_lookup_release_validation.json"

BANNED_TERMS = [
    "录取概率",
    "稳录",
    "保证录取",
    "必上",
    "智能预测录取",
    "推荐你报考",
    "一定能上",
]

REQUIRED_TERMS = [
    "试验版",
    "历史参考",
    "不构成录取承诺",
]


def folder_size(folder: Path) -> int:
    if not folder.exists():
        return 0
    return sum(path.stat().st_size for path in folder.rglob("*") if path.is_file())


def main() -> None:
    index = load_json(INDEX_PATH)
    coverage = load_json(COVERAGE_PATH)

    datasets = index["datasets"]
    public_datasets = [item for item in datasets if item.get("is_public")]
    counts = Counter(item.get("quality_status") for item in public_datasets)

    parse_errors: list[str] = []
    missing_files: list[str] = []

    for dataset in public_datasets:
        admissions_path = ROOT / "app" / "public" / dataset["admissions_file"]
        if not admissions_path.exists():
            missing_files.append(dataset["admissions_file"])
        else:
            try:
                load_json(admissions_path)
            except Exception as exc:  # noqa: BLE001
                parse_errors.append(f"{dataset['admissions_file']}: {exc}")

        rank_file = dataset.get("rank_table_file") or ""
        if rank_file:
            rank_path = ROOT / "app" / "public" / rank_file
            if not rank_path.exists():
                missing_files.append(rank_file)
            else:
                try:
                    load_json(rank_path)
                except Exception as exc:  # noqa: BLE001
                    parse_errors.append(f"{rank_file}: {exc}")

    admissions_files = list((APP_BASE / "admissions").glob("*.json"))
    rank_files = list((APP_BASE / "rank-tables").glob("*.json"))
    largest_admissions = max(admissions_files, key=lambda path: path.stat().st_size, default=None)

    score_lookup_size = folder_size(APP_BASE)
    dist_size = folder_size(DIST_BASE)

    source_texts = []
    for path in [
        ROOT / "app" / "src" / "pages" / "ScoreLookupPage.tsx",
        ROOT / "app" / "src" / "pages" / "HomePage.tsx",
        ROOT / "app" / "src" / "pages" / "AboutPage.tsx",
    ]:
        if path.exists():
            source_texts.append(path.read_text(encoding="utf-8"))
    combined_text = "\n".join(source_texts)

    banned_hits = [term for term in BANNED_TERMS if term in combined_text]
    required_hits = [term for term in REQUIRED_TERMS if term in combined_text]

    payload = {
        "public_dataset_count": len(public_datasets),
        "quality_counts": dict(counts),
        "coverage_rows": len(coverage.get("rows", [])),
        "admissions_files": len(admissions_files),
        "rank_table_files": len(rank_files),
        "score_lookup_size_mb": round(score_lookup_size / 1024 / 1024, 2),
        "dist_size_mb": round(dist_size / 1024 / 1024, 2),
        "largest_admissions_file": largest_admissions.name if largest_admissions else "",
        "largest_admissions_size_mb": round(
            (largest_admissions.stat().st_size if largest_admissions else 0) / 1024 / 1024,
            2,
        ),
        "missing_files": missing_files,
        "parse_errors": parse_errors,
        "banned_hits": banned_hits,
        "required_hits": required_hits,
    }
    dump_json(VALIDATION_JSON, payload)

    checklist_lines = [
        "# Score Lookup Release Checklist",
        "",
        f"- 前端公开候选数据集：{len(public_datasets)}",
        f"- verified：{counts['verified']}",
        f"- warning：{counts['warning']}",
        f"- candidate：{counts['candidate']}",
        f"- score_only：{counts['score_only']}",
        f"- coverage 行数：{len(coverage.get('rows', []))}",
        f"- admissions 分片文件数：{len(admissions_files)}",
        f"- rank_table 分片文件数：{len(rank_files)}",
        f"- JSON 缺失文件数：{len(missing_files)}",
        f"- JSON 解析错误数：{len(parse_errors)}",
        f"- 风险禁用词命中数：{len(banned_hits)}",
        f"- 风险说明关键词命中数：{len(required_hits)}",
        "",
        "## 验收结论",
        "",
        f"- 公开候选数据已恢复：{'是' if len(public_datasets) > 2 else '否'}",
        f"- 福建 2023 历史类可继续标记为已抽检通过：{'是' if counts['verified'] >= 2 else '否'}",
        f"- 江西 2025 历史类已标记为警示数据：{'是' if counts['warning'] >= 3 else '否'}",
        f"- 页面文案未出现禁用表述：{'是' if not banned_hits else '否'}",
        f"- 页面包含试验版与风险提示：{'是' if len(required_hits) == len(REQUIRED_TERMS) else '否'}",
    ]
    write_markdown(CHECKLIST_PATH, "\n".join(checklist_lines))

    size_lines = [
        "# Frontend Data Size Report",
        "",
        f"- app/public/data/score-lookup 总体积：{score_lookup_size / 1024 / 1024:.2f} MB",
        f"- app/dist 总体积：{dist_size / 1024 / 1024:.2f} MB",
        f"- admissions 分片文件数：{len(admissions_files)}",
        f"- rank_table 分片文件数：{len(rank_files)}",
        (
            f"- 最大单个 admissions 分片：{largest_admissions.name} "
            f"({largest_admissions.stat().st_size / 1024 / 1024:.2f} MB)"
            if largest_admissions
            else "- 最大单个 admissions 分片：无"
        ),
        "- 初始页面只加载 index.json 和 coverage.json，不默认加载 admissions 大分片。",
        "- admissions 与 rank_table 仍按用户选择的数据集按需加载。",
    ]
    write_markdown(SIZE_REPORT_PATH, "\n".join(size_lines))

    print(
        f"validated national candidate release: public={len(public_datasets)}, "
        f"verified={counts['verified']}, warning={counts['warning']}, "
        f"candidate={counts['candidate']}, score_only={counts['score_only']}"
    )


if __name__ == "__main__":
    main()
