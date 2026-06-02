from __future__ import annotations

import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "app" / "public" / "data"
REPORT_PATH = ROOT / "docs" / "school_tag_validation_report.md"

SCHOOLS_PATH = DATA_DIR / "schools.json"
ENRICHED_PATH = DATA_DIR / "schools.enriched.json"
SCHOOL_TAGS_PATH = DATA_DIR / "school_tags.json"

EXPECTED_985 = 39
EXPECTED_211 = 112
EXPECTED_DFC = 147


def load_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def to_markdown_counter(counter: Counter[str], limit: int = 30) -> list[str]:
    lines: list[str] = []
    for key, value in counter.most_common(limit):
        label = key if key else "(空字符串)"
        lines.append(f"| {label} | {value} |")
    if not lines:
        lines.append("| 无 | 0 |")
    return lines


def main() -> None:
    if not ENRICHED_PATH.exists():
        raise FileNotFoundError(f"Missing file: {ENRICHED_PATH}")

    schools = load_json(SCHOOLS_PATH)
    enriched = load_json(ENRICHED_PATH)
    school_tags = load_json(SCHOOL_TAGS_PATH)

    school_ids = [item["school_id"] for item in enriched]
    unique_school_ids = len(set(school_ids))

    count_985 = sum(1 for item in enriched if item["is_985"])
    count_211 = sum(1 for item in enriched if item["is_211"])
    count_dfc = sum(1 for item in enriched if item["is_double_first_class"])

    school_type_counter = Counter(item["school_type"] for item in enriched)
    ownership_counter = Counter(item["ownership"] for item in enriched)
    province_counter = Counter(item["province"] for item in enriched)

    school_type_uncertain = [
        item["school_name"] for item in enriched if not item["school_type"] or item["school_type"] == "其他"
    ]
    ownership_uncertain = [
        item["school_name"] for item in enriched if not item["ownership"] or item["ownership"] == "其他"
    ]
    empty_tag_sources = [item["school_name"] for item in enriched if not item.get("tag_sources")]

    normalized_current = {item["school_name"] for item in enriched}
    unmatched_985 = [item["school_name"] for item in school_tags if item["is_985"] and item["school_name"] not in normalized_current]
    unmatched_211 = [item["school_name"] for item in school_tags if item["is_211"] and item["school_name"] not in normalized_current]
    unmatched_dfc = [item["school_name"] for item in school_tags if item["is_double_first_class"] and item["school_name"] not in normalized_current]

    lines: list[str] = []
    lines.append("# 院校标签校验报告")
    lines.append("")
    lines.append(f"- 处理时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("- 输入文件：")
    lines.append("  - `app/public/data/schools.json`")
    lines.append("  - `app/public/data/school_tags.json`")
    lines.append("- 输出文件：")
    lines.append("  - `app/public/data/schools.enriched.json`")
    lines.append("  - `docs/school_tag_validation_report.md`")
    lines.append("")
    lines.append("## 总量检查")
    lines.append("")
    lines.append(f"- `schools.json` 总数：{len(schools)}")
    lines.append(f"- `schools.enriched.json` 总数：{len(enriched)}")
    lines.append(f"- `school_id` 唯一数：{unique_school_ids}")
    lines.append(f"- 条数是否一致：{'是' if len(schools) == len(enriched) else '否'}")
    lines.append(f"- `school_id` 是否仍然唯一：{'是' if unique_school_ids == len(enriched) else '否'}")
    lines.append("")
    lines.append("## 核心标签统计")
    lines.append("")
    lines.append(f"- 985 数量：{count_985}（官方名单 {EXPECTED_985} 所）")
    lines.append(f"- 211 数量：{count_211}（官方名单常见口径 {EXPECTED_211} 所）")
    lines.append(f"- 双一流数量：{count_dfc}（官方名单 {EXPECTED_DFC} 所）")
    lines.append("- 说明：当前数据是按 `schools.json` 中的学校名称实体匹配，部分京校/异地校区被拆成独立学校名，而部分军队院校未出现在底表中，因此不应把当前计数直接当作官方口径复刻。")
    lines.append("")
    lines.append("## school_type 分布")
    lines.append("")
    lines.append("| school_type | count |")
    lines.append("|---|---:|")
    lines.extend(to_markdown_counter(school_type_counter))
    lines.append("")
    lines.append("## ownership 分布")
    lines.append("")
    lines.append("| ownership | count |")
    lines.append("|---|---:|")
    lines.extend(to_markdown_counter(ownership_counter))
    lines.append("")
    lines.append("## province 分布（前 20）")
    lines.append("")
    lines.append("| province | count |")
    lines.append("|---|---:|")
    lines.extend(to_markdown_counter(province_counter, 20))
    lines.append("")
    lines.append("## 可疑匹配列表")
    lines.append("")
    lines.append(f"- 官方 985 名单中未出现在 `schools.json` 的学校：{len(unmatched_985)}")
    for name in unmatched_985[:20]:
        lines.append(f"  - {name}")
    lines.append(f"- 官方 211 名单中未出现在 `schools.json` 的学校：{len(unmatched_211)}")
    for name in unmatched_211[:20]:
        lines.append(f"  - {name}")
    lines.append(f"- 官方双一流名单中未出现在 `schools.json` 的学校：{len(unmatched_dfc)}")
    for name in unmatched_dfc[:20]:
        lines.append(f"  - {name}")
    lines.append("")
    lines.append("## 未确认字段列表")
    lines.append("")
    lines.append(f"- `school_type` 为空或 `其他` 的学校数：{len(school_type_uncertain)}")
    for name in school_type_uncertain[:30]:
        lines.append(f"  - {name}")
    lines.append(f"- `ownership` 为空或 `其他` 的学校数：{len(ownership_uncertain)}")
    for name in ownership_uncertain[:30]:
        lines.append(f"  - {name}")
    lines.append(f"- `tag_sources` 为空的学校数：{len(empty_tag_sources)}")
    for name in empty_tag_sources[:30]:
        lines.append(f"  - {name}")
    lines.append("")
    lines.append("## 结论")
    lines.append("")
    lines.append("- 当前数据足够进入网页 MVP 的院校查询页面开发，支持 985/211/双一流、层次、类型、办学性质等基础筛选。")
    lines.append("- 当前标签仍不是百分百准确，尤其 `school_type` 属于名称关键词弱规则推断，适合作为前端辅助筛选，不应当被当作严格事实标签。")
    lines.append("- `school_type = 其他` 的学校仍然很多，说明名称关键词推断较保守；如果要提升筛选体验，仍建议后续补标准院校类型表。")
    lines.append("- 若后续要提升专业侧体验，优先级更高的补充项是 `subject_requirement`（选科要求）与更可靠的院校类型/官网数据。")

    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Validation report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
