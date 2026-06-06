from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from national_extraction_common import (
    PROVINCES,
    completion_rate,
    dump_json,
    iso_now,
    load_json,
    normalize_text,
    safe_float,
    safe_int,
    write_markdown,
)

ROOT = Path(__file__).resolve().parents[1]
DATA_WORK = ROOT / "data_work"
APP_DATA = ROOT / "app" / "public" / "data" / "score-lookup"
ADMISSIONS_DIR = APP_DATA / "admissions"
RANK_DIR = APP_DATA / "rank-tables"
MAX_SHARD_BYTES = 8 * 1024 * 1024
VALID_SUBJECTS = {"历史类", "物理类", "文科", "理科", "综合", "体育类"}
ADMISSIONS_SOURCES = [
    DATA_WORK / "national_admissions_normalized",
    DATA_WORK / "remaining_admissions_normalized",
    DATA_WORK / "backfill_admissions_normalized",
]
RANK_SOURCES = [
    DATA_WORK / "national_rank_tables_normalized",
    DATA_WORK / "backfill_rank_tables_normalized",
]


def ensure_dirs() -> None:
    ADMISSIONS_DIR.mkdir(parents=True, exist_ok=True)
    RANK_DIR.mkdir(parents=True, exist_ok=True)


def is_valid_province(value: str) -> bool:
    return normalize_text(value) in PROVINCES


def is_valid_subject(value: str) -> bool:
    return normalize_text(value) in VALID_SUBJECTS


def load_remaining_completed_admissions() -> set[str]:
    path = DATA_WORK / "remaining_extraction_progress.json"
    if not path.exists():
        return set()
    progress = load_json(path).get("tasks", [])
    return {
        Path(task["output_file"]).name
        for task in progress
        if task.get("document_type") == "admissions" and task.get("status") == "completed"
    }


def load_allowed_backfill_files(summary_name: str) -> set[str]:
    path = DATA_WORK / summary_name
    if not path.exists():
        return set()
    summary = load_json(path)
    rows = summary.get("rows", [])
    return {
        Path(row["output_file"]).name
        for row in rows
        if row.get("status") in {"completed", "skipped_existing"}
    }


def compact_admission(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "school_code": normalize_text(record.get("school_code")),
        "school_name": normalize_text(record.get("school_name")),
        "major_group_code": normalize_text(record.get("major_group_code")),
        "major_group_name": normalize_text(record.get("major_group_name")),
        "major_code": normalize_text(record.get("major_code")),
        "major_name": normalize_text(record.get("major_name")),
        "min_score": safe_float(record.get("min_score")),
        "min_rank": safe_int(record.get("min_rank")),
        "batch": normalize_text(record.get("batch")),
        "remarks": normalize_text(record.get("remarks")),
        "source_file": normalize_text(record.get("source_file")),
        "confidence": normalize_text(record.get("confidence")) or "low",
    }


def compact_rank(record: dict[str, Any]) -> dict[str, Any] | None:
    score = safe_float(record.get("score"))
    rank = safe_int(record.get("rank"))
    if score is None or rank is None:
        return None
    return {
        "score": score,
        "rank": rank,
        "same_score_count": safe_int(record.get("same_score_count")),
        "cumulative_count": safe_int(record.get("cumulative_count")),
    }


def dedupe_admissions(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    result = []
    for record in records:
        key = (
            record.get("school_code"),
            record.get("school_name"),
            record.get("major_group_code"),
            record.get("major_group_name"),
            record.get("major_code"),
            record.get("major_name"),
            record.get("min_score"),
            record.get("min_rank"),
            record.get("batch"),
        )
        if key in seen:
            continue
        seen.add(key)
        result.append(record)
    return result


def build_admissions_map() -> dict[tuple[str, int, str, str], list[dict[str, Any]]]:
    result: dict[tuple[str, int, str, str], list[dict[str, Any]]] = defaultdict(list)
    remaining_completed = load_remaining_completed_admissions()
    backfill_completed = load_allowed_backfill_files("score_lookup_backfill_admissions_summary.json")
    for folder in ADMISSIONS_SOURCES:
        if not folder.exists():
            continue
        for path in folder.glob("*.json"):
            if folder.name == "remaining_admissions_normalized" and path.name not in remaining_completed:
                continue
            if folder.name == "backfill_admissions_normalized" and path.name not in backfill_completed:
                continue
            records = load_json(path)
            if not isinstance(records, list) or not records:
                continue
            year = safe_int(records[0].get("year"))
            province = normalize_text(records[0].get("province"))
            subject_type = normalize_text(records[0].get("subject_type"))
            batch = normalize_text(records[0].get("batch"))
            if year is None:
                continue
            key = (province, year, subject_type, batch)
            result[key].extend(compact_admission(record) for record in records)
    for key in list(result):
        result[key] = dedupe_admissions(result[key])
    return result


def build_rank_map() -> dict[tuple[str, int, str], list[dict[str, Any]]]:
    result: dict[tuple[str, int, str], list[dict[str, Any]]] = defaultdict(list)
    backfill_completed = load_allowed_backfill_files("score_lookup_backfill_rank_summary.json")
    for folder in RANK_SOURCES:
        if not folder.exists():
            continue
        for path in folder.glob("*.json"):
            if folder.name == "backfill_rank_tables_normalized" and path.name not in backfill_completed:
                continue
            records = load_json(path)
            if not isinstance(records, list) or not records:
                continue
            year = safe_int(records[0].get("year"))
            province = normalize_text(records[0].get("province"))
            subject_type = normalize_text(records[0].get("subject_type"))
            if year is None:
                continue
            key = (province, year, subject_type)
            for record in records:
                compacted = compact_rank(record)
                if compacted is not None:
                    result[key].append(compacted)
    cleaned: dict[tuple[str, int, str], list[dict[str, Any]]] = {}
    for key, records in result.items():
        by_score: dict[float, dict[str, Any]] = {}
        for record in records:
            score = float(record["score"])
            existing = by_score.get(score)
            if existing is None or int(record["rank"]) < int(existing["rank"]):
                by_score[score] = record
        cleaned[key] = sorted(by_score.values(), key=lambda item: (-float(item["score"]), int(item["rank"])))
    return cleaned


def enrich_admissions_with_rank(records: list[dict[str, Any]], rank_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not records or not rank_records:
        return records
    score_to_rank: dict[float, int] = {}
    for item in rank_records:
        score = safe_float(item.get("score"))
        rank = safe_int(item.get("rank"))
        if score is None or rank is None:
            continue
        current = score_to_rank.get(score)
        if current is None or rank < current:
            score_to_rank[score] = rank
    enriched = []
    for record in records:
        item = dict(record)
        if item.get("min_rank") is None:
            score = safe_float(item.get("min_score"))
            if score is not None and score in score_to_rank:
                item["min_rank"] = score_to_rank[score]
                remarks = normalize_text(item.get("remarks"))
                item["remarks"] = f"{remarks};rank_from_rank_table".strip(";")
                if item.get("confidence") == "low":
                    item["confidence"] = "medium"
        enriched.append(item)
    return enriched


def admissions_metrics(records: list[dict[str, Any]]) -> dict[str, float]:
    total = len(records)
    min_score_rate = completion_rate(records, "min_score")
    min_rank_rate = completion_rate(records, "min_rank")
    low_rate = sum(1 for record in records if record.get("confidence") == "low") / max(total, 1)
    trace_rate = completion_rate(records, "source_file")
    scores = [float(record["min_score"]) for record in records if record.get("min_score") is not None]
    ranks = [int(record["min_rank"]) for record in records if record.get("min_rank") is not None]
    abnormal_score = any(score < 0 or score > 1000 for score in scores)
    abnormal_rank = any(rank < 0 or rank > 10_000_000 for rank in ranks)
    return {
        "records": total,
        "min_score_complete_rate": min_score_rate,
        "min_rank_complete_rate": min_rank_rate,
        "low_confidence_rate": low_rate,
        "source_traceable_rate": trace_rate,
        "abnormal": 1.0 if abnormal_score or abnormal_rank else 0.0,
    }


def rank_metrics(records: list[dict[str, Any]]) -> dict[str, float]:
    total = len(records)
    score_rate = completion_rate(records, "score")
    rank_rate = completion_rate(records, "rank")
    monotonic_issue = 0
    for prev, curr in zip(records, records[1:]):
        if float(curr["score"]) < float(prev["score"]) and int(curr["rank"]) < int(prev["rank"]):
            monotonic_issue += 1
    return {
        "records": total,
        "score_complete_rate": score_rate,
        "rank_complete_rate": rank_rate,
        "monotonic_issue": float(monotonic_issue),
    }


def grade(adm_metrics: dict[str, float], rank_data_present: bool) -> str:
    if not rank_data_present:
        return "C"
    if adm_metrics["min_score_complete_rate"] >= 0.95 and adm_metrics["min_rank_complete_rate"] >= 0.9:
        return "A"
    if adm_metrics["min_score_complete_rate"] >= 0.85 and adm_metrics["min_rank_complete_rate"] >= 0.75:
        return "B"
    return "C"


def shard_admissions(dataset_id: str, records: list[dict[str, Any]]) -> tuple[str, int]:
    payload = json.dumps(records, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(payload) <= MAX_SHARD_BYTES:
        out_path = ADMISSIONS_DIR / f"{dataset_id}.json"
        out_path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
        return f"data/score-lookup/admissions/{out_path.name}", len(payload)

    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        school_name = normalize_text(record.get("school_name"))
        bucket = school_name[:1] if school_name else "_"
        buckets[bucket].append(record)

    shard_files: list[str] = []
    max_size = 0
    for idx, (_, bucket_records) in enumerate(sorted(buckets.items()), start=1):
        shard_name = f"{dataset_id}__part{idx}.json"
        shard_path = ADMISSIONS_DIR / shard_name
        shard_path.write_text(json.dumps(bucket_records, ensure_ascii=False), encoding="utf-8")
        shard_size = shard_path.stat().st_size
        max_size = max(max_size, shard_size)
        shard_files.append(f"data/score-lookup/admissions/{shard_name}")

    manifest_path = ADMISSIONS_DIR / f"{dataset_id}.json"
    manifest_path.write_text(
        json.dumps({"dataset_id": dataset_id, "shards": shard_files, "total_records": len(records)}, ensure_ascii=False),
        encoding="utf-8",
    )
    return f"data/score-lookup/admissions/{manifest_path.name}", max_size


def write_rank_file(dataset_key: tuple[str, int, str], records: list[dict[str, Any]]) -> str:
    province, year, subject_type = dataset_key
    file_name = f"{province}_{year}_{subject_type}.json"
    out_path = RANK_DIR / file_name
    out_path.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
    return f"data/score-lookup/rank-tables/{file_name}"


def build() -> dict[str, Any]:
    ensure_dirs()
    admissions_map = build_admissions_map()
    rank_map = build_rank_map()

    datasets = []
    excluded = []
    max_shard_size = 0
    admissions_shard_count = 0
    rank_shard_files: set[str] = set()

    for (province, year, subject_type, batch), admissions_records in sorted(admissions_map.items()):
        if not is_valid_province(province) or not is_valid_subject(subject_type) or year is None:
            excluded.append(
                {
                    "province": province,
                    "year": year,
                    "subject_type": subject_type,
                    "batch": batch,
                    "reason": "invalid province/year/subject",
                }
            )
            continue
        if len(admissions_records) < 100:
            excluded.append(
                {
                    "province": province,
                    "year": year,
                    "subject_type": subject_type,
                    "batch": batch,
                    "reason": "admissions records < 100",
                }
            )
            continue

        rank_records = rank_map.get((province, year, subject_type), [])
        admissions_records = enrich_admissions_with_rank(admissions_records, rank_records)
        adm_metrics = admissions_metrics(admissions_records)
        rank_data_metrics = (
            rank_metrics(rank_records)
            if rank_records
            else {"records": 0, "score_complete_rate": 0.0, "rank_complete_rate": 0.0, "monotonic_issue": 1.0}
        )

        enabled = (
            adm_metrics["records"] >= 100
            and rank_data_metrics["records"] >= 100
            and adm_metrics["min_score_complete_rate"] >= 0.8
            and adm_metrics["min_rank_complete_rate"] >= 0.7
            and rank_data_metrics["score_complete_rate"] >= 0.95
            and rank_data_metrics["rank_complete_rate"] >= 0.95
            and adm_metrics["low_confidence_rate"] <= 0.35
            and adm_metrics["source_traceable_rate"] >= 0.9
            and adm_metrics["abnormal"] == 0
            and rank_data_metrics["monotonic_issue"] == 0
        )

        notes = ""
        if not rank_records:
            notes = "historical_score_only"
        elif adm_metrics["min_rank_complete_rate"] < 0.7:
            notes = "historical_score_only"
        elif not enabled:
            notes = "quality_below_frontend_threshold"

        dataset_id = f"{province}_{year}_{subject_type}_{batch or 'all'}"
        admissions_file, shard_size = shard_admissions(dataset_id, admissions_records)
        max_shard_size = max(max_shard_size, shard_size)
        admissions_shard_count += 1

        rank_file = ""
        if rank_records:
            rank_file = write_rank_file((province, year, subject_type), rank_records)
            rank_shard_files.add(rank_file)

        datasets.append(
            {
                "dataset_id": dataset_id,
                "province": province,
                "year": year,
                "subject_type": subject_type,
                "batch": batch,
                "admissions_file": admissions_file,
                "rank_table_file": rank_file,
                "admissions_records": adm_metrics["records"],
                "rank_table_records": rank_data_metrics["records"],
                "min_score_complete_rate": round(adm_metrics["min_score_complete_rate"], 4),
                "min_rank_complete_rate": round(adm_metrics["min_rank_complete_rate"], 4),
                "score_complete_rate": round(rank_data_metrics["score_complete_rate"], 4),
                "rank_complete_rate": round(rank_data_metrics["rank_complete_rate"], 4),
                "quality_grade": grade(adm_metrics, bool(rank_records)),
                "enabled": enabled,
                "notes": notes,
            }
        )

    index = {
        "generated_at": iso_now(),
        "version": "score_lookup_demo_v1",
        "notice": "本数据仅供历史录取参考，不构成录取承诺。",
        "datasets": datasets,
    }
    dump_json(APP_DATA / "index.json", index)

    total_size = sum(path.stat().st_size for path in APP_DATA.rglob("*.json"))
    report = {
        "dataset_count": len(datasets),
        "enabled_count": sum(1 for item in datasets if item["enabled"]),
        "admissions_shard_count": admissions_shard_count,
        "rank_table_shard_count": len(rank_shard_files),
        "max_shard_size_bytes": max_shard_size,
        "total_size_bytes": total_size,
        "excluded_count": len(excluded),
        "excluded": excluded[:200],
        "datasets": datasets,
    }
    dump_json(DATA_WORK / "frontend_score_lookup_build_summary.json", report)

    lines = [
        "# Frontend Score Lookup Data Report",
        "",
        f"- 进入前端的数据集数量：{len(datasets)}",
        f"- enabled=true 数据集数量：{sum(1 for item in datasets if item['enabled'])}",
        f"- admissions 前端分片数量：{admissions_shard_count}",
        f"- rank_table 前端分片数量：{len(rank_shard_files)}",
        f"- 最大分片文件大小：{max_shard_size / 1024 / 1024:.2f} MB",
        f"- 总前端数据体积：{total_size / 1024 / 1024:.2f} MB",
        f"- 被排除的数据集数量：{len(excluded)}",
        "- 被排除原因：非法 province/year/subject、admissions 记录不足、字段质量不足。",
        f"- 是否存在性能风险：{'是' if max_shard_size > MAX_SHARD_BYTES else '否'}",
    ]
    write_markdown(ROOT / "docs" / "frontend_score_lookup_data_report.md", "\n".join(lines))
    return report


def main() -> None:
    report = build()
    print(
        f"Built {report['dataset_count']} frontend datasets, "
        f"{report['enabled_count']} enabled, "
        f"max shard {report['max_shard_size_bytes'] / 1024 / 1024:.2f} MB"
    )


if __name__ == "__main__":
    main()
