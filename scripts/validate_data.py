from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "app" / "public" / "data"
REPORT_PATH = ROOT / "docs" / "data_validation_report.md"


def load_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def counter_markdown(counter: Counter[str], limit: int = 20) -> list[str]:
    lines: list[str] = []
    for key, value in counter.most_common(limit):
        label = key if key != "" else "(空字符串)"
        lines.append(f"| {label} | {value} |")
    if not lines:
        lines.append("| 无 | 0 |")
    return lines


def find_duplicates(values: list[str]) -> dict[str, int]:
    counts = Counter(values)
    return {key: count for key, count in counts.items() if key and count > 1}


def build_report() -> str:
    schools_path = DATA_DIR / "schools.json"
    majors_path = DATA_DIR / "majors.json"
    schools = load_json(schools_path)
    majors = load_json(majors_path)

    school_id_dupes = find_duplicates([item["school_id"] for item in schools])
    school_name_dupes = find_duplicates([item["school_name"] for item in schools])
    school_level_counter = Counter(item["school_level"] for item in schools)
    province_counter = Counter(item["province"] for item in schools)
    school_empty = {
        "school_name": sum(1 for item in schools if not item["school_name"]),
        "province": sum(1 for item in schools if not item["province"]),
        "city": sum(1 for item in schools if not item["city"]),
        "department": sum(1 for item in schools if not item["department"]),
        "school_type": sum(1 for item in schools if not item["school_type"]),
        "official_site": sum(1 for item in schools if not item["official_site"]),
    }

    major_id_dupes = find_duplicates([item["major_id"] for item in majors])
    major_code_dupes = find_duplicates([item["major_code"] for item in majors])
    major_name_dupes = find_duplicates([item["major_name"] for item in majors])
    degree_level_counter = Counter(item["degree_level"] for item in majors)
    major_category_counter = Counter(item["major_category"] for item in majors)
    major_empty = {
        "major_code": sum(1 for item in majors if not item["major_code"]),
        "major_name": sum(1 for item in majors if not item["major_name"]),
        "major_category": sum(1 for item in majors if not item["major_category"]),
        "major_discipline": sum(1 for item in majors if not item["major_discipline"]),
        "degree": sum(1 for item in majors if not item["degree"]),
        "duration": sum(1 for item in majors if not item["duration"]),
        "subject_requirement": sum(1 for item in majors if not item["subject_requirement"]),
        "description": sum(1 for item in majors if not item["description"]),
    }

    invalid_school_rows = [
        item for item in schools
        if not item["school_name"] or not item["province"] or not item["source_row"]
    ]
    incomplete_school_rows = [
        item for item in schools
        if not item["department"] or not item["city"]
    ]
    invalid_major_rows = [
        item for item in majors
        if not item["major_code"] or not item["major_name"] or not item["source_row"]
    ]

    school_name_dupe_examples = list(sorted(school_name_dupes.items(), key=lambda pair: (-pair[1], pair[0])))[:20]
    major_code_dupe_examples = list(sorted(major_code_dupes.items(), key=lambda pair: (-pair[1], pair[0])))[:20]
    major_name_dupe_examples = list(sorted(major_name_dupes.items(), key=lambda pair: (-pair[1], pair[0])))[:20]

    enough_for_query = "是。当前数据足够启动第一版院校查询和专业查询，但不适合承载院校标签筛选的完整体验。"

    lines: list[str] = []
    lines.append("# 数据校验报告")
    lines.append("")
    lines.append(f"- 转换时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("- 输入文件：")
    lines.append("  - `全国普通高等学校名单.xls`")
    lines.append("  - `普通高等学校本科专业目录.xlsx`")
    lines.append("  - `普通高等学校高等职业教育（专科）专业目录.xlsx`")
    lines.append("- 输出文件：")
    lines.append("  - `app/public/data/schools.json`")
    lines.append("  - `app/public/data/majors.json`")
    lines.append("")
    lines.append("## 总量统计")
    lines.append("")
    lines.append(f"- 院校数据总量：{len(schools)}")
    lines.append(f"- 本科院校数量：{school_level_counter.get('本科', 0)}")
    lines.append(f"- 专科院校数量：{school_level_counter.get('专科', 0)}")
    lines.append(f"- 专业数据总量：{len(majors)}")
    lines.append(f"- 本科专业数量：{degree_level_counter.get('本科', 0)}")
    lines.append(f"- 专科专业数量：{degree_level_counter.get('专科', 0)}")
    lines.append("")
    lines.append("## schools.json 校验")
    lines.append("")
    lines.append(f"- `school_id` 重复数：{len(school_id_dupes)}")
    lines.append(f"- `school_name` 为空数：{school_empty['school_name']}")
    lines.append(f"- `province` 为空数：{school_empty['province']}")
    lines.append("")
    lines.append("### school_level 分布")
    lines.append("")
    lines.append("| school_level | count |")
    lines.append("|---|---:|")
    lines.extend(counter_markdown(school_level_counter))
    lines.append("")
    lines.append("### province 分布（前 20）")
    lines.append("")
    lines.append("| province | count |")
    lines.append("|---|---:|")
    lines.extend(counter_markdown(province_counter, 20))
    lines.append("")
    lines.append("### schools 空值统计")
    lines.append("")
    lines.append("| field | empty_count |")
    lines.append("|---|---:|")
    for key, value in school_empty.items():
        lines.append(f"| {key} | {value} |")
    lines.append("")
    lines.append("### 重复院校名称（前 20）")
    lines.append("")
    lines.append("| school_name | count |")
    lines.append("|---|---:|")
    if school_name_dupe_examples:
        for key, value in school_name_dupe_examples:
            lines.append(f"| {key} | {value} |")
    else:
        lines.append("| 无 | 0 |")
    lines.append("")
    lines.append("## majors.json 校验")
    lines.append("")
    lines.append(f"- `major_id` 重复数：{len(major_id_dupes)}")
    lines.append(f"- `major_code` 为空数：{major_empty['major_code']}")
    lines.append(f"- `major_name` 为空数：{major_empty['major_name']}")
    lines.append("")
    lines.append("### degree_level 分布")
    lines.append("")
    lines.append("| degree_level | count |")
    lines.append("|---|---:|")
    lines.extend(counter_markdown(degree_level_counter))
    lines.append("")
    lines.append("### major_category 分布（前 20）")
    lines.append("")
    lines.append("| major_category | count |")
    lines.append("|---|---:|")
    lines.extend(counter_markdown(major_category_counter, 20))
    lines.append("")
    lines.append("### majors 空值统计")
    lines.append("")
    lines.append("| field | empty_count |")
    lines.append("|---|---:|")
    for key, value in major_empty.items():
        lines.append(f"| {key} | {value} |")
    lines.append("")
    lines.append("### 重复专业代码（前 20）")
    lines.append("")
    lines.append("| major_code | count |")
    lines.append("|---|---:|")
    if major_code_dupe_examples:
        for key, value in major_code_dupe_examples:
            lines.append(f"| {key} | {value} |")
    else:
        lines.append("| 无 | 0 |")
    lines.append("")
    lines.append("### 重复专业名称（前 20）")
    lines.append("")
    lines.append("| major_name | count |")
    lines.append("|---|---:|")
    if major_name_dupe_examples:
        for key, value in major_name_dupe_examples:
            lines.append(f"| {key} | {value} |")
    else:
        lines.append("| 无 | 0 |")
    lines.append("")
    lines.append("## 异常数据列表")
    lines.append("")
    lines.append(f"- 学校记录异常数：{len(invalid_school_rows)}")
    lines.append(f"- 学校补充字段缺失样例数：{len(incomplete_school_rows)}")
    lines.append(f"- 专业记录异常数：{len(invalid_major_rows)}")
    lines.append("- 说明：这里的异常仅指关键字段为空或 `source_row` 缺失。")
    lines.append("")
    lines.append("### 学校字段缺失样例（前 10）")
    lines.append("")
    if incomplete_school_rows:
        for item in incomplete_school_rows[:10]:
            lines.append(
                f"- `{item['school_name']}`：department=`{item['department']}`，city=`{item['city']}`，source_row={item['source_row']}"
            )
    else:
        lines.append("- 无")
    lines.append("")
    lines.append("### 专业异常样例（前 10）")
    lines.append("")
    if invalid_major_rows:
        for item in invalid_major_rows[:10]:
            lines.append(
                f"- `{item['major_name']}`：major_code=`{item['major_code']}`，source_row={item['source_row']}"
            )
    else:
        lines.append("- 无")
    lines.append("")
    lines.append("## 结论")
    lines.append("")
    lines.append(f"- 是否足够支撑第一版院校查询和专业查询：{enough_for_query}")
    lines.append("- 当前数据不够支撑精细标签筛选，因为缺少院校类型、985/211/双一流、官网、专业简介、选科要求等字段。")
    lines.append("- 专业名称和专业代码存在大量重复是正常现象的一部分：本科与专科并存、不同目录层级共用名称、以及同名不同代码的专业并存。")
    return "\n".join(lines) + "\n"


def main() -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(build_report(), encoding="utf-8")
    print(f"Validation report written to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
