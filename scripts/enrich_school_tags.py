from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import pdfplumber


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "app" / "public" / "data"

SCHOOLS_PATH = DATA_DIR / "schools.json"
SCHOOL_TAGS_PATH = DATA_DIR / "school_tags.json"
ENRICHED_PATH = DATA_DIR / "schools.enriched.json"
DOUBLE_FIRST_CLASS_PDF = ROOT / "tmp_double_first_class.pdf"

SOURCE_985 = "教育部“985工程”学校名单（2008-04-25） https://www.moe.gov.cn/srcsite/A22/s7065/200612/t20061206_128833.html"
SOURCE_211 = "教育部“211工程”学校名单（2008-04-25） https://www.moe.gov.cn/srcsite/A22/s7065/200512/t20051223_82762.html"
SOURCE_DFC = '教育部第二轮“双一流”建设高校及建设学科名单（2022-02-11） https://www.moe.gov.cn/srcsite/A22/s7065/202202/t20220211_598710.html'


OFFICIAL_985 = {
    "北京大学",
    "中国人民大学",
    "清华大学",
    "北京航空航天大学",
    "北京理工大学",
    "中国农业大学",
    "北京师范大学",
    "中央民族大学",
    "南开大学",
    "天津大学",
    "大连理工大学",
    "东北大学",
    "吉林大学",
    "哈尔滨工业大学",
    "复旦大学",
    "同济大学",
    "上海交通大学",
    "华东师范大学",
    "南京大学",
    "东南大学",
    "浙江大学",
    "中国科学技术大学",
    "厦门大学",
    "山东大学",
    "中国海洋大学",
    "武汉大学",
    "华中科技大学",
    "湖南大学",
    "中南大学",
    "中山大学",
    "华南理工大学",
    "四川大学",
    "重庆大学",
    "电子科技大学",
    "西安交通大学",
    "西北工业大学",
    "西北农林科技大学",
    "兰州大学",
    "国防科学技术大学",
}


OFFICIAL_211 = {
    "北京大学",
    "清华大学",
    "中国人民大学",
    "北京交通大学",
    "北京工业大学",
    "北京航空航天大学",
    "北京理工大学",
    "北京科技大学",
    "北京化工大学",
    "北京邮电大学",
    "中国农业大学",
    "北京林业大学",
    "北京中医药大学",
    "北京师范大学",
    "北京外国语大学",
    "中国传媒大学",
    "中央财经大学",
    "对外经济贸易大学",
    "北京体育大学",
    "中央音乐学院",
    "中国政法大学",
    "华北电力大学",
    "中央民族大学",
    "中国矿业大学（北京）",
    "中国石油大学（北京）",
    "中国地质大学（北京）",
    "南开大学",
    "天津大学",
    "天津医科大学",
    "河北工业大学",
    "太原理工大学",
    "内蒙古大学",
    "辽宁大学",
    "大连理工大学",
    "东北大学",
    "大连海事大学",
    "吉林大学",
    "东北师范大学",
    "延边大学",
    "哈尔滨工业大学",
    "哈尔滨工程大学",
    "东北农业大学",
    "东北林业大学",
    "复旦大学",
    "同济大学",
    "上海交通大学",
    "华东理工大学",
    "东华大学",
    "华东师范大学",
    "上海外国语大学",
    "上海财经大学",
    "上海大学",
    "第二军医大学",
    "南京大学",
    "东南大学",
    "苏州大学",
    "南京航空航天大学",
    "南京理工大学",
    "中国矿业大学",
    "河海大学",
    "江南大学",
    "南京农业大学",
    "中国药科大学",
    "南京师范大学",
    "浙江大学",
    "安徽大学",
    "中国科学技术大学",
    "合肥工业大学",
    "厦门大学",
    "福州大学",
    "南昌大学",
    "山东大学",
    "中国海洋大学",
    "中国石油大学（华东）",
    "郑州大学",
    "武汉大学",
    "华中科技大学",
    "中国地质大学（武汉）",
    "武汉理工大学",
    "华中师范大学",
    "华中农业大学",
    "中南财经政法大学",
    "湖南大学",
    "中南大学",
    "湖南师范大学",
    "国防科学技术大学",
    "中山大学",
    "暨南大学",
    "华南理工大学",
    "华南师范大学",
    "广西大学",
    "海南大学",
    "重庆大学",
    "西南大学",
    "四川大学",
    "西南交通大学",
    "电子科技大学",
    "四川农业大学",
    "西南财经大学",
    "贵州大学",
    "云南大学",
    "西藏大学",
    "西北大学",
    "西安交通大学",
    "西北工业大学",
    "西安电子科技大学",
    "长安大学",
    "陕西师范大学",
    "西北农林科技大学",
    "第四军医大学",
    "兰州大学",
    "青海大学",
    "宁夏大学",
    "新疆大学",
    "石河子大学",
}


ALIASES: dict[str, list[str]] = {
    "国防科学技术大学": ["中国人民解放军国防科技大学", "国防科技大学"],
    "第二军医大学": ["中国人民解放军第二军医大学", "海军军医大学"],
    "第四军医大学": ["中国人民解放军第四军医大学", "空军军医大学"],
    "北京协和医学院": ["中国协和医科大学"],
}

CANONICAL_NAME_MAP = {
    "国防科技大学": "国防科学技术大学",
    "海军军医大学": "第二军医大学",
    "空军军医大学": "第四军医大学",
}


TYPE_RULES: list[tuple[str, str]] = [
    ("师范", "师范"),
    ("医科", "医药"),
    ("中医药", "医药"),
    ("药科", "医药"),
    ("医学院", "医药"),
    ("医药", "医药"),
    ("卫生", "医药"),
    ("财经", "财经"),
    ("经济", "财经"),
    ("金融", "财经"),
    ("商学院", "财经"),
    ("商业", "财经"),
    ("理工", "理工"),
    ("工业", "理工"),
    ("科技", "理工"),
    ("工程", "理工"),
    ("电子科技", "理工"),
    ("邮电", "理工"),
    ("电力", "理工"),
    ("海事", "理工"),
    ("铁道", "理工"),
    ("铁路", "理工"),
    ("农业", "农林"),
    ("农林", "农林"),
    ("林业", "农林"),
    ("政法", "政法"),
    ("公安", "政法"),
    ("警察", "政法"),
    ("司法", "政法"),
    ("外国语", "语言"),
    ("语言", "语言"),
    ("美术", "艺术"),
    ("音乐", "艺术"),
    ("艺术", "艺术"),
    ("戏剧", "艺术"),
    ("电影", "艺术"),
    ("传媒", "艺术"),
    ("舞蹈", "艺术"),
    ("体育", "体育"),
    ("民族", "民族"),
    ("军", "军事"),
]


def load_json(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_school_name(name: str) -> str:
    return (
        name.replace("（", "(")
        .replace("）", ")")
        .replace(" ", "")
        .strip()
    )


def parse_double_first_class_pdf() -> dict[str, list[str]]:
    entries: dict[str, list[str]] = {}
    lines: list[str] = []
    with pdfplumber.open(str(DOUBLE_FIRST_CLASS_PDF)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                line = "".join(line.split())
                if line:
                    lines.append(line)

    current_school = ""
    current_text = ""
    for line in lines:
        if line.startswith("附件") or "第二轮“双一流”建设高校及建设学科名单" in line or line == "（按学校代码排序）":
            continue
        if "：" in line:
            if current_school:
                entries[current_school] = discipline_text_to_list(current_text)
            school, disciplines = line.split("：", 1)
            current_school = CANONICAL_NAME_MAP.get(school.strip(), school.strip())
            current_text = disciplines.strip()
        else:
            if current_school:
                current_text += line.strip()
    if current_school:
        entries[current_school] = discipline_text_to_list(current_text)
    return entries


def discipline_text_to_list(text: str) -> list[str]:
    if not text or "自主确定建设学科并自行公布" in text:
        return []
    cleaned = text.replace("，", "、").replace("；", "、").strip("、")
    disciplines = [part.strip() for part in cleaned.split("、") if part.strip()]
    return disciplines


def build_school_tag_records() -> tuple[list[dict[str, Any]], dict[str, list[str]]]:
    double_first = parse_double_first_class_pdf()
    all_names = sorted(OFFICIAL_985 | OFFICIAL_211 | set(double_first.keys()))
    records: list[dict[str, Any]] = []
    source_map: dict[str, list[str]] = {}

    for name in all_names:
        sources: list[str] = []
        if name in OFFICIAL_985:
            sources.append(SOURCE_985)
        if name in OFFICIAL_211:
            sources.append(SOURCE_211)
        if name in double_first:
            sources.append(SOURCE_DFC)
        source_map[name] = sources
        records.append(
            {
                "school_name": name,
                "aliases": ALIASES.get(name, []),
                "is_985": name in OFFICIAL_985,
                "is_211": name in OFFICIAL_211,
                "is_double_first_class": name in double_first,
                "double_first_class_disciplines": double_first.get(name, []),
                "source": " | ".join(sources),
                "notes": "" if name not in ALIASES else "存在别名映射",
            }
        )
    return records, source_map


def infer_school_type(school_name: str, school_level: str) -> tuple[str, str]:
    for keyword, inferred_type in TYPE_RULES:
        if keyword in school_name:
            return inferred_type, f"school_type:名称关键词推断({keyword})"
    if school_level == "本科" and school_name.endswith("大学"):
        return "综合", "school_type:弱规则回退(本科大学→综合)"
    return "其他", "school_type:未命中关键词(回退为其他)"


def build_tags(record: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    if record["is_985"]:
        tags.append("985")
    if record["is_211"]:
        tags.append("211")
    if record["is_double_first_class"]:
        tags.append("双一流")
    if record["school_level"]:
        tags.append(record["school_level"])
    if record["school_type"]:
        tags.append(record["school_type"])
    if record["ownership"]:
        tags.append(record["ownership"])
    seen: set[str] = set()
    unique_tags: list[str] = []
    for tag in tags:
        if tag not in seen:
            unique_tags.append(tag)
            seen.add(tag)
    return unique_tags


def enrich_schools() -> tuple[list[dict[str, Any]], list[str]]:
    schools = load_json(SCHOOLS_PATH)
    tag_records, _ = build_school_tag_records()
    write_json(SCHOOL_TAGS_PATH, tag_records)

    match_map: dict[str, dict[str, Any]] = {}
    alias_map: dict[str, dict[str, Any]] = {}
    for record in tag_records:
        match_map[normalize_school_name(record["school_name"])] = record
        for alias in record["aliases"]:
            alias_map[normalize_school_name(alias)] = record

    logs: list[str] = []
    enriched: list[dict[str, Any]] = []
    matched_count = 0

    for school in schools:
        school_name = school["school_name"]
        normalized = normalize_school_name(school_name)
        tag_record = match_map.get(normalized) or alias_map.get(normalized)
        tag_sources: list[str] = []

        if tag_record:
            matched_count += 1
            if tag_record["is_985"]:
                tag_sources.append(SOURCE_985)
            if tag_record["is_211"]:
                tag_sources.append(SOURCE_211)
            if tag_record["is_double_first_class"]:
                tag_sources.append(SOURCE_DFC)

        school_type, school_type_source = infer_school_type(school_name, school.get("school_level", ""))
        tag_sources.append(school_type_source)

        ownership = school.get("ownership", "") or "其他"
        if school.get("ownership"):
            tag_sources.append("ownership:沿用schools.json")
        else:
            tag_sources.append("ownership:原始字段缺失(回退为其他)")

        enriched_record = {
            **school,
            "school_type": school_type,
            "ownership": ownership,
            "is_985": bool(tag_record and tag_record["is_985"]),
            "is_211": bool(tag_record and tag_record["is_211"]),
            "is_double_first_class": bool(tag_record and tag_record["is_double_first_class"]),
            "double_first_class_disciplines": list(tag_record["double_first_class_disciplines"]) if tag_record else [],
            "tags": [],
            "official_site": school.get("official_site", ""),
            "tag_sources": tag_sources,
        }
        enriched_record["tags"] = build_tags(enriched_record)
        enriched.append(enriched_record)

    official_names = {record["school_name"] for record in tag_records}
    normalized_current = {normalize_school_name(item["school_name"]) for item in schools}
    unmatched_official = []
    for record in tag_records:
        official_name = record["school_name"]
        keys = [normalize_school_name(official_name)] + [normalize_school_name(alias) for alias in record["aliases"]]
        if not any(key in normalized_current for key in keys):
            unmatched_official.append(official_name)

    logs.append(f"schools total: {len(schools)}")
    logs.append(f"official tag records: {len(tag_records)}")
    logs.append(f"schools matched to tag table: {matched_count}")
    logs.append(f"official tagged schools not found in schools.json: {len(unmatched_official)}")
    logs.extend(f"unmatched official school: {name}" for name in unmatched_official[:20])

    write_json(ENRICHED_PATH, enriched)
    return enriched, logs


def main() -> None:
    enriched, logs = enrich_schools()
    print(f"school_tags.json: {SCHOOL_TAGS_PATH}")
    print(f"schools.enriched.json: {ENRICHED_PATH}")
    print(f"enriched count: {len(enriched)}")
    print("Logs:")
    for line in logs:
        print(f"- {line}")


if __name__ == "__main__":
    main()
