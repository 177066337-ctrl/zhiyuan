import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


ROOT_DIR = Path(r"D:\2026\zhiyuan\高考志Y系列资料")
OUTPUT_JSON = Path(r"D:\2026\zhiyuan\data_work\resource_inventory.json")
OUTPUT_MD = Path(r"D:\2026\zhiyuan\docs\resource_inventory_full.md")

PROVINCES = [
    "北京",
    "天津",
    "上海",
    "重庆",
    "河北",
    "山西",
    "辽宁",
    "吉林",
    "黑龙江",
    "江苏",
    "浙江",
    "安徽",
    "福建",
    "江西",
    "山东",
    "河南",
    "湖北",
    "湖南",
    "广东",
    "广西",
    "海南",
    "四川",
    "贵州",
    "云南",
    "西藏",
    "陕西",
    "甘肃",
    "青海",
    "宁夏",
    "新疆",
    "内蒙古",
]

DOCUMENT_TYPE_RULES = [
    ("一分一段表", [r"一分一段", r"分段统计", r"成绩分段", r"分数段统计"]),
    ("招生计划", [r"招生计划", r"计划数", r"招生专业目录", r"招生目录"]),
    ("专业选科要求", [r"选科要求", r"选考科目", r"首选科目", r"再选科目"]),
    ("录取统计", [r"录取统计", r"投档", r"调档线", r"录取日报", r"分数线", r"最低分", r"最低位次", r"录取最低分"]),
    ("招生章程", [r"招生章程"]),
    ("院校资料", [r"学校名单", r"大学", r"院校", r"学校", r"学科评估"]),
    ("专业资料", [r"专业目录", r"专业解读", r"专业介绍", r"专业"]),
]


@dataclass
class ResourceRecord:
    file_path: str
    file_name: str
    extension: str
    size_mb: float
    modified_time: str
    likely_year: str
    likely_province: str
    likely_subject_type: str
    likely_document_type: str
    extractability: str
    reason: str
    recommended_next_action: str


def iter_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file():
            yield path


def detect_year(text: str) -> str:
    years = re.findall(r"20\d{2}", text)
    if years:
        return years[0]
    short = re.findall(r"(?<!\d)(2[3-9])(?!\d)", text)
    if short:
        return f"20{short[0]}"
    return "未知"


def detect_province(text: str) -> str:
    for province in PROVINCES:
        if province in text:
            return province
    return "未知"


def detect_subject_type(text: str) -> str:
    if "历史类" in text:
        return "历史类"
    if "物理类" in text:
        return "物理类"
    if "文科" in text or "文史" in text:
        return "文科"
    if "理科" in text or "理工" in text:
        return "理科"
    if "综合" in text:
        return "综合"
    return "未知"


def detect_document_type(text: str) -> str:
    for doc_type, patterns in DOCUMENT_TYPE_RULES:
        for pattern in patterns:
            if re.search(pattern, text):
                return doc_type
    return "其他"


def detect_extractability(path: Path, doc_type: str) -> tuple[str, str, str]:
    ext = path.suffix.lower()
    if ext in {".xlsx", ".xls", ".csv"}:
        return "高", "结构化表格格式，可直接读取 sheet、表头和样例行。", "优先探测表头与关键字段。"
    if ext == ".pdf":
        if doc_type in {"录取统计", "一分一段表", "招生计划", "专业选科要求"}:
            return "中", "PDF 可能可抽文本或表格，但稳定性依赖排版。", "抽样读取前 2 页并判断是否需要 OCR。"
        return "低", "说明型 PDF 偏多，结构化成本通常较高。", "仅在确认为核心数据源时再抽样。"
    if ext in {".doc", ".docx", ".ppt", ".pptx"}:
        if doc_type in {"录取统计", "一分一段表", "招生计划", "专业选科要求"}:
            return "中", "Office 文档可提取文本或表格，但稳定性受版式影响。", "提取标题、段落或表格前几行确认。"
        return "低", "多为说明材料，不是首选结构化来源。", "只保留参考，不优先抽取。"
    if ext in {".txt", ".htm", ".html", ".xml"}:
        return "高", "文本或标记格式通常可直接解析。", "检查是否包含结构化字段。"
    if ext in {".png", ".jpg", ".jpeg"}:
        return "低", "图片文件需要 OCR，当前阶段不做全量 OCR。", "仅对极少数核心文件手动抽样。"
    return "未知", "暂未定义的文件类型。", "后续按需人工确认。"


def build_record(path: Path) -> ResourceRecord:
    name_text = f"{path.name} {path.as_posix()}"
    doc_type = detect_document_type(name_text)
    extractability, reason, next_action = detect_extractability(path, doc_type)
    return ResourceRecord(
        file_path=str(path),
        file_name=path.name,
        extension=path.suffix.lower() or "",
        size_mb=round(path.stat().st_size / (1024 * 1024), 3),
        modified_time=datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
        likely_year=detect_year(name_text),
        likely_province=detect_province(name_text),
        likely_subject_type=detect_subject_type(name_text),
        likely_document_type=doc_type,
        extractability=extractability,
        reason=reason,
        recommended_next_action=next_action,
    )


def count_by(records: list[ResourceRecord], field: str) -> Counter:
    return Counter(getattr(record, field) for record in records)


def top_candidates(records: list[ResourceRecord], doc_type: str, limit: int = 30) -> list[ResourceRecord]:
    matched = [r for r in records if r.likely_document_type == doc_type]
    matched.sort(key=lambda r: (r.likely_year, r.likely_province, r.file_name))
    return matched[:limit]


def not_recommended(records: list[ResourceRecord], limit: int = 30) -> list[ResourceRecord]:
    items = [
        r
        for r in records
        if r.extension in {".png", ".jpg", ".jpeg"} or (r.likely_document_type == "其他" and r.extractability in {"低", "未知"})
    ]
    items.sort(key=lambda r: (-r.size_mb, r.file_name))
    return items[:limit]


def render_counter(counter: Counter, title: str) -> list[str]:
    lines = [f"## {title}", ""]
    for key, value in counter.most_common():
        lines.append(f"- `{key}`: {value}")
    lines.append("")
    return lines


def write_markdown(records: list[ResourceRecord]) -> None:
    total_size_mb = sum(r.size_mb for r in records)
    total_size_gib = total_size_mb / 1024
    lines: list[str] = [
        "# 资源全量清单",
        "",
        f"- 扫描目录：`{ROOT_DIR}`",
        f"- 扫描时间：`{datetime.now().isoformat(timespec='seconds')}`",
        f"- 文件总数：`{len(records)}`",
        f"- 总大小：`{total_size_mb:.2f} MB`（约 `{total_size_gib:.2f} GiB`）",
        "",
    ]
    lines.extend(render_counter(count_by(records, "extension"), "按扩展名统计"))
    lines.extend(render_counter(count_by(records, "likely_year"), "按年份统计"))
    lines.extend(render_counter(count_by(records, "likely_document_type"), "按资料类型统计"))

    sections = [
        ("录取数据核心候选文件", "录取统计"),
        ("一分一段核心候选文件", "一分一段表"),
        ("招生计划核心候选文件", "招生计划"),
        ("选科要求核心候选文件", "专业选科要求"),
    ]
    for title, doc_type in sections:
        lines.append(f"## {title}")
        lines.append("")
        candidates = top_candidates(records, doc_type)
        if not candidates:
            lines.append("- 无")
        else:
            for item in candidates:
                lines.append(
                    f"- `{item.file_path}` | `{item.likely_year}` | `{item.likely_province}` | `{item.likely_subject_type}` | `{item.extractability}`"
                )
        lines.append("")

    lines.append("## 不建议优先处理的文件")
    lines.append("")
    for item in not_recommended(records):
        lines.append(f"- `{item.file_path}` | `{item.extension}` | `{item.size_mb:.2f} MB` | `{item.reason}`")
    lines.append("")

    OUTPUT_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    records = [build_record(path) for path in iter_files(ROOT_DIR)]
    OUTPUT_JSON.write_text(
        json.dumps([asdict(record) for record in records], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    write_markdown(records)
    print(f"Scanned {len(records)} files into {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
