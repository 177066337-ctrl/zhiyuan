from __future__ import annotations

import json
import math
import re
import time
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import pdfplumber

try:
    import openpyxl  # type: ignore
except Exception:  # pragma: no cover
    openpyxl = None

try:
    import xlrd  # type: ignore
except Exception:  # pragma: no cover
    xlrd = None

ROOT = Path(__file__).resolve().parents[1]
DATA_WORK = ROOT / "data_work"
RAW_ROOT = ROOT / "\u9ad8\u8003\u5fd7Y\u7cfb\u5217\u8d44\u6599"

DOC_ADMISSIONS = "admissions"
DOC_RANK = "rank_table"
DOC_PLANS = "plans"
DOC_SUBJECT_REQ = "subject_requirement"
DOC_UNKNOWN = "unknown"

TYPE_MAP = {
    "\u5f55\u53d6\u7edf\u8ba1": DOC_ADMISSIONS,
    "\u4e00\u5206\u4e00\u6bb5\u8868": DOC_RANK,
    "\u62db\u751f\u8ba1\u5212": DOC_PLANS,
    "\u4e13\u4e1a\u9009\u79d1\u8981\u6c42": DOC_SUBJECT_REQ,
}

PROVINCES = [
    "\u5317\u4eac",
    "\u5929\u6d25",
    "\u6cb3\u5317",
    "\u5c71\u897f",
    "\u5185\u8499\u53e4",
    "\u8fbd\u5b81",
    "\u5409\u6797",
    "\u9ed1\u9f99\u6c5f",
    "\u4e0a\u6d77",
    "\u6c5f\u82cf",
    "\u6d59\u6c5f",
    "\u5b89\u5fbd",
    "\u798f\u5efa",
    "\u6c5f\u897f",
    "\u5c71\u4e1c",
    "\u6cb3\u5357",
    "\u6e56\u5317",
    "\u6e56\u5357",
    "\u5e7f\u4e1c",
    "\u5e7f\u897f",
    "\u6d77\u5357",
    "\u91cd\u5e86",
    "\u56db\u5ddd",
    "\u8d35\u5dde",
    "\u4e91\u5357",
    "\u897f\u85cf",
    "\u9655\u897f",
    "\u7518\u8083",
    "\u9752\u6d77",
    "\u5b81\u590f",
    "\u65b0\u7586",
]

SUBJECT_PATTERNS = [
    ("\u5386\u53f2\u7c7b", "\u5386\u53f2\u7c7b"),
    ("\u7269\u7406\u7c7b", "\u7269\u7406\u7c7b"),
    ("\u6587\u79d1", "\u6587\u79d1"),
    ("\u7406\u79d1", "\u7406\u79d1"),
    ("\u7efc\u5408", "\u7efc\u5408"),
    ("\u4f53\u80b2\u7c7b", "\u4f53\u80b2\u7c7b"),
    ("\u827a\u672f\u7c7b", "\u827a\u672f\u7c7b"),
    ("\u4e09\u6821\u751f\u7c7b", "\u4e09\u6821\u751f\u7c7b"),
]

BATCH_PATTERNS = [
    "\u666e\u901a\u672c\u79d1\u6279",
    "\u672c\u79d1\u6279",
    "\u672c\u79d1\u4e00\u6279",
    "\u672c\u79d1\u4e8c\u6279",
    "\u672c\u79d1\u4e09\u6279",
    "\u672c\u79d1\u63d0\u524d\u6279",
    "\u9ad8\u804c\u4e13\u79d1\u6279",
    "\u4e13\u79d1\u6279",
    "\u9ad8\u804c\u6279",
    "\u4e13\u79d1\u63d0\u524d\u6279",
    "\u666e\u901a\u6279",
    "\u5e73\u884c\u5fd7\u613f",
    "\u5f81\u96c6\u5fd7\u613f",
    "\u519b\u961f",
    "\u56fd\u5bb6\u4e13\u9879",
]

HEADER_SYNONYMS = {
    "school_code": [
        "\u9662\u6821\u4ee3\u53f7",
        "\u9662\u6821\u4ee3\u7801",
        "\u5b66\u6821\u4ee3\u53f7",
        "\u5b66\u6821\u4ee3\u7801",
        "\u9662\u6821\u4ee3\u7801",
    ],
    "school_name": [
        "\u9662\u6821\u540d\u79f0",
        "\u5b66\u6821\u540d\u79f0",
        "\u9662\u6821",
        "\u5b66\u6821",
        "\u9662\u6821\u3001\u4e13\u4e1a\u7ec4\uff08\u518d\u9009\u79d1\u76ee\u8981\u6c42\uff09",
    ],
    "major_group_code": [
        "\u4e13\u4e1a\u7ec4\u4ee3\u7801",
        "\u4e13\u4e1a\u7ec4\u4ee3\u53f7",
        "\u4e13\u4e1a\u7ec4\u4ee3\u7801",
    ],
    "major_group_name": [
        "\u4e13\u4e1a\u7ec4",
        "\u4e13\u4e1a\u7ec4\u540d\u79f0",
        "\u9662\u6821\u4e13\u4e1a\u7ec4",
    ],
    "major_code": [
        "\u4e13\u4e1a\u4ee3\u7801",
        "\u4e13\u4e1a\u4ee3\u53f7",
    ],
    "major_name": [
        "\u4e13\u4e1a\u540d\u79f0",
        "\u4e13\u4e1a",
    ],
    "min_score": [
        "\u6700\u4f4e\u5206",
        "\u6295\u6863\u6700\u4f4e\u5206",
        "\u5f55\u53d6\u6700\u4f4e\u5206",
        "\u6295\u6863\u7ebf",
        "\u6295\u6863\u5206",
        "\u5206\u6570",
    ],
    "min_rank": [
        "\u6700\u4f4e\u4f4d\u6b21",
        "\u6295\u6863\u6392\u540d",
        "\u4f4d\u6b21",
        "\u6392\u540d",
    ],
    "avg_score": [
        "\u5e73\u5747\u5206",
    ],
    "max_score": [
        "\u6700\u9ad8\u5206",
    ],
    "plan_count": [
        "\u8ba1\u5212\u6570",
        "\u62db\u751f\u8ba1\u5212",
        "\u8ba1\u5212",
    ],
    "admission_count": [
        "\u5f55\u53d6\u4eba\u6570",
        "\u5f55\u53d6\u6570",
    ],
    "same_score_count": [
        "\u672c\u6bb5\u4eba\u6570",
        "\u540c\u5206\u4eba\u6570",
    ],
    "cumulative_count": [
        "\u7d2f\u8ba1\u4eba\u6570",
        "\u7d2f\u8ba1",
        "\u7d2f\u52a0\u4eba\u6570",
    ],
    "rank": [
        "\u4f4d\u6b21",
        "\u7d2f\u8ba1\u4eba\u6570",
        "\u6392\u540d",
    ],
    "score": [
        "\u5206\u6570\u6bb5",
        "\u5206\u6570",
        "\u6210\u7ee9",
    ],
}

TEXT_SCORE_RE = re.compile(r"(?<!\d)(\d{2,3})(?:\.(\d{1,9}))?(?!\d)")
TEXT_RANK_RE = re.compile(r"(?<!\d)(\d{1,7})(?!\d)")
YEAR_RE = re.compile(r"(20\d{2})")


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_json(path: Path) -> Any:
    last_error: Exception | None = None
    for _ in range(3):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            last_error = exc
            time.sleep(0.05)
    if last_error is not None:
        raise last_error
    raise ValueError(f"failed to read json: {path}")


def dump_json(path: Path, data: Any) -> None:
    ensure_dir(path.parent)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp_path.replace(path)


def iso_now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""
    text = str(value).replace("\r", " ").replace("\n", " ").replace("\t", " ")
    text = re.sub(r"\s+", " ", text).strip()
    if text in {"nan", "None", "null"}:
        return ""
    return text


def to_number(value: Any) -> int | float | None:
    text = normalize_text(value)
    if not text:
        return None
    text = text.replace(",", "")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    num_text = match.group(0)
    if "." in num_text:
        try:
            return float(num_text)
        except ValueError:
            return None
    try:
        return int(num_text)
    except ValueError:
        return None


def has_any(text: str, needles: Iterable[str]) -> bool:
    return any(needle in text for needle in needles)


def slugify(*parts: str) -> str:
    safe = []
    for part in parts:
        text = normalize_text(part) or "unknown"
        text = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", text, flags=re.UNICODE)
        safe.append(text.strip("_") or "unknown")
    return "_".join(safe)


def detect_year(text: str, fallback: str = "") -> str:
    matches = YEAR_RE.findall(text)
    if matches:
        return matches[-1]
    return fallback or ""


def detect_province(text: str, fallback: str = "") -> str:
    for province in PROVINCES:
        if province in text:
            return province
    return fallback or "\u672a\u77e5"


def detect_subject_type(text: str, fallback: str = "") -> str:
    for keyword, label in SUBJECT_PATTERNS:
        if keyword in text:
            return label
    return fallback or "\u672a\u77e5"


def detect_batch(text: str) -> str:
    for pattern in BATCH_PATTERNS:
        if pattern in text:
            return pattern
    if "\u672c\u79d1" in text:
        return "\u672c\u79d1"
    if "\u4e13\u79d1" in text or "\u9ad8\u804c" in text:
        return "\u4e13\u79d1"
    return ""


def map_document_type(text: str, fallback: str = DOC_UNKNOWN) -> str:
    for key, mapped in TYPE_MAP.items():
        if key in text:
            return mapped
    return fallback


def to_lower_ext(path: str) -> str:
    return Path(path).suffix.lower()


def extension_family(ext: str) -> str:
    if ext in {".xls", ".xlsx", ".csv"}:
        return "table"
    if ext == ".pdf":
        return "pdf"
    if ext in {".doc", ".docx"}:
        return "doc"
    if ext in {".htm", ".html", ".txt"}:
        return "text"
    if ext in {".png", ".jpg", ".jpeg"}:
        return "image"
    return "other"


def candidate_text(item: dict[str, Any]) -> str:
    return " ".join(
        [
            normalize_text(item.get("file_path")),
            normalize_text(item.get("file_name")),
            normalize_text(item.get("likely_province")),
            normalize_text(item.get("likely_subject_type")),
            normalize_text(item.get("likely_document_type")),
            normalize_text(item.get("reason")),
        ]
    )


def is_pdf_text_extractable(item: dict[str, Any]) -> bool:
    probe = item.get("probe") or {}
    sample_pages = probe.get("sample_pages") or []
    text_len = 0
    for page in sample_pages:
        text_len += len(normalize_text(page.get("text")))
    return not probe.get("needs_ocr") and text_len >= 50


def priority_from_item(item: dict[str, Any], document_type: str) -> str:
    ext = to_lower_ext(item["file_path"])
    family = extension_family(ext)
    text = candidate_text(item)
    has_core_fields = has_any(
        text,
        [
            "\u6700\u4f4e\u5206",
            "\u6295\u6863\u7ebf",
            "\u6295\u6863\u6700\u4f4e\u5206",
            "\u6700\u4f4e\u4f4d\u6b21",
            "\u4f4d\u6b21",
            "\u4e00\u5206\u4e00\u6bb5",
            "\u5206\u6570\u6bb5",
            "\u7d2f\u8ba1\u4eba\u6570",
        ],
    )
    has_clear_meta = (
        normalize_text(item.get("likely_province")) not in {"", "\u672a\u77e5"}
        and normalize_text(item.get("likely_year")) not in {"", "\u672a\u77e5"}
        and normalize_text(item.get("likely_subject_type")) not in {"", "\u672a\u77e5"}
    )
    extractability = normalize_text(item.get("extractability"))
    feasibility = normalize_text(item.get("structured_feasibility"))

    if family == "image":
        return "low"
    if ext == ".txt":
        return "low"
    if document_type in {DOC_ADMISSIONS, DOC_RANK} and family == "table" and has_core_fields:
        return "high" if has_clear_meta or feasibility == "\u9ad8" else "medium"
    if document_type in {DOC_ADMISSIONS, DOC_RANK} and ext == ".pdf" and is_pdf_text_extractable(item):
        return "high" if has_clear_meta and has_core_fields else "medium"
    if extractability == "\u9ad8" and has_core_fields:
        return "medium"
    return "low"


def selected_from_priority(priority: str, requires_ocr: bool) -> tuple[bool, str]:
    if priority == "low":
        return False, "low_priority"
    if requires_ocr:
        return False, "requires_ocr"
    return True, ""


def is_manual_review_needed(item: dict[str, Any], priority: str, requires_ocr: bool) -> bool:
    if requires_ocr:
        return True
    if priority == "medium":
        return True
    ext = to_lower_ext(item["file_path"])
    return ext in {".pdf", ".doc", ".docx", ".htm", ".html", ".txt"}


def read_excel_rows(path: Path, max_rows: int | None = None) -> dict[str, list[list[str]]]:
    rows_by_sheet: dict[str, list[list[str]]] = {}
    ext = path.suffix.lower()
    if ext == ".xlsx":
        if openpyxl is None:
            return rows_by_sheet
        wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
        for ws in wb.worksheets:
            rows: list[list[str]] = []
            for idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
                rows.append([normalize_text(cell) for cell in row])
                if max_rows and idx >= max_rows:
                    break
            rows_by_sheet[ws.title] = rows
        wb.close()
        return rows_by_sheet
    if ext == ".xls":
        if xlrd is None:
            return rows_by_sheet
        book = xlrd.open_workbook(path)
        for name in book.sheet_names():
            sh = book.sheet_by_name(name)
            rows = []
            nrows = sh.nrows if max_rows is None else min(sh.nrows, max_rows)
            for r in range(nrows):
                rows.append([normalize_text(value) for value in sh.row_values(r)])
            rows_by_sheet[name] = rows
        return rows_by_sheet
    return rows_by_sheet


def fill_right(row: list[str]) -> list[str]:
    result: list[str] = []
    last = ""
    for cell in row:
        text = normalize_text(cell)
        if text:
            last = text
            result.append(text)
        else:
            result.append(last)
    return result


def detect_header_span(rows: list[list[str]], target_fields: Iterable[str]) -> tuple[int, int, dict[int, str]]:
    target_set = set(target_fields)
    best_score = -1
    best = (0, 0, {})
    preview_limit = min(10, len(rows))
    max_width = max((len(r) for r in rows[:preview_limit]), default=0)
    for start in range(preview_limit):
        for depth in range(1, 4):
            if start + depth > len(rows):
                continue
            merged: dict[int, str] = {}
            for col in range(max_width):
                pieces = []
                for rr in rows[start : start + depth]:
                    if col < len(rr):
                        val = normalize_text(rr[col])
                        if val:
                            pieces.append(val)
                merged[col] = " ".join(dict.fromkeys(pieces))
            mapped = map_headers(merged)
            score = len(set(mapped.values()) & target_set)
            if score > best_score:
                best_score = score
                best = (start, start + depth - 1, mapped)
    return best


def map_headers(headers: dict[int, str]) -> dict[int, str]:
    mapped: dict[int, str] = {}
    for col, header in headers.items():
        text = normalize_text(header)
        if not text:
            continue
        for field, keywords in HEADER_SYNONYMS.items():
            if any(keyword in text for keyword in keywords):
                mapped[col] = field
                break
    return mapped


def row_has_payload(row: list[str]) -> bool:
    non_empty = [cell for cell in row if normalize_text(cell)]
    if not non_empty:
        return False
    joined = " ".join(non_empty)
    return bool(TEXT_SCORE_RE.search(joined) or re.search(r"[\u4e00-\u9fff]{2,}", joined))


def safe_float(value: Any) -> float | None:
    num = to_number(value)
    if num is None:
        return None
    return float(num)


def safe_int(value: Any) -> int | None:
    num = to_number(value)
    if num is None:
        return None
    return int(round(float(num)))


def split_school_group_text(text: str) -> tuple[str, str]:
    clean = normalize_text(text)
    if not clean:
        return "", ""
    patterns = [
        r"^(?P<school>.+?)(?P<group>第[A-Z0-9一二三四五六七八九十百零〇]{1,6}组.*)$",
        r"^(?P<school>.+?)(?P<group>[A-Z]?\d{2,4}\s*专业组.*)$",
        r"^(?P<school>.+?)(?P<group>\d{2,4}\s*专业组.*)$",
    ]
    for pattern in patterns:
        match = re.match(pattern, clean)
        if match:
            return normalize_text(match.group("school")), normalize_text(match.group("group"))
    return clean, ""


def classify_confidence(*, school_name: str, score: Any = None, rank: Any = None) -> str:
    if school_name and score is not None and rank is not None:
        return "high"
    if school_name and (score is not None or rank is not None):
        return "medium"
    if score is not None or rank is not None:
        return "low"
    return "low"


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_None_"
    head = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(normalize_text(row.get(col)) for col in columns) + " |")
    return "\n".join([head, sep, *body])


def summarize_counter(counter: Counter[Any]) -> list[dict[str, Any]]:
    return [{"key": key, "count": count} for key, count in counter.most_common()]


def extract_pdf_text(path: Path, max_pages: int | None = None) -> list[dict[str, Any]]:
    pages: list[dict[str, Any]] = []
    with pdfplumber.open(path) as pdf:
        page_count = len(pdf.pages)
        limit = page_count if max_pages is None else min(page_count, max_pages)
        for index in range(limit):
            page = pdf.pages[index]
            text = page.extract_text() or ""
            tables = page.extract_tables() or []
            pages.append(
                {
                    "page": index + 1,
                    "text": text,
                    "tables": tables,
                }
            )
    return pages


def is_score_like(num: float | None) -> bool:
    return num is not None and 0 <= num <= 1000


def is_rank_like(num: int | None) -> bool:
    return num is not None and 0 <= num <= 10_000_000


def source_ok(record: dict[str, Any]) -> bool:
    return bool(normalize_text(record.get("source_file"))) and (
        record.get("source_row") is not None or record.get("source_page") is not None
    )


def completion_rate(records: list[dict[str, Any]], field: str) -> float:
    if not records:
        return 0.0
    ok = 0
    for record in records:
        value = record.get(field)
        if value not in (None, "", []):
            ok += 1
    return ok / len(records)


def grouped_files_by_task_id(tasks: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {task["task_id"]: task for task in tasks}


def guess_ready_reason(metrics: dict[str, Any]) -> str:
    if metrics.get("ready_for_score_lookup_demo"):
        return "admissions and rank table both pass minimum completeness thresholds"
    issues = metrics.get("blocking_issues") or []
    return "; ".join(issues[:4])


def write_markdown(path: Path, text: str) -> None:
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")
