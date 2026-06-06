from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from national_extraction_common import (
    DATA_WORK,
    completion_rate,
    dump_json,
    ensure_dir,
    guess_ready_reason,
    iso_now,
    load_json,
    markdown_table,
    normalize_text,
    safe_float,
    source_ok,
    summarize_counter,
    write_markdown,
)


ADMISSIONS_DIR = DATA_WORK / "national_admissions_normalized"
RANK_DIR = DATA_WORK / "national_rank_tables_normalized"
REPORT_DIR = ensure_dir(DATA_WORK / "national_validation_reports")


def load_normalized(dir_path: Path) -> dict[str, list[dict]]:
    result = {}
    if not dir_path.exists():
        return result
    for path in sorted(dir_path.glob("*.normalized.json")):
        result[path.stem.replace(".normalized", "")] = load_json(path)
    return result


def admissions_metrics(records: list[dict]) -> dict:
    scores = [r["min_score"] for r in records if r.get("min_score") is not None]
    ranks = [r["min_rank"] for r in records if r.get("min_rank") is not None]
    duplicate_keys = Counter(
        (
            normalize_text(r.get("school_code")),
            normalize_text(r.get("school_name")),
            normalize_text(r.get("major_group_name")),
            normalize_text(r.get("major_name")),
            r.get("min_score"),
            r.get("min_rank"),
        )
        for r in records
    )
    duplicates = sum(count - 1 for count in duplicate_keys.values() if count > 1)
    abnormal_scores = sum(1 for s in scores if s < 0 or s > 1000)
    abnormal_ranks = sum(1 for r in ranks if r < 0 or r > 10000000)
    return {
        "records": len(records),
        "school_name_empty": sum(1 for r in records if not normalize_text(r.get("school_name"))),
        "min_score_empty": sum(1 for r in records if r.get("min_score") is None),
        "min_rank_empty": sum(1 for r in records if r.get("min_rank") is None),
        "min_score_range": [min(scores) if scores else None, max(scores) if scores else None],
        "min_rank_range": [min(ranks) if ranks else None, max(ranks) if ranks else None],
        "duplicates": duplicates,
        "abnormal_scores": abnormal_scores,
        "abnormal_ranks": abnormal_ranks,
        "confidence_distribution": dict(Counter(r.get("confidence", "unknown") for r in records)),
        "source_traceable_rate": completion_rate(
            [{"traceable": 1 if source_ok(r) else None} for r in records],
            "traceable",
        ),
    }


def rank_metrics(records: list[dict]) -> dict:
    scores = [r["score"] for r in records if r.get("score") is not None]
    ranks = [r["rank"] for r in records if r.get("rank") is not None]
    score_duplicates = len(scores) - len(set(scores))
    sorted_records = sorted(
        [r for r in records if r.get("score") is not None and r.get("rank") is not None],
        key=lambda x: (-float(x["score"]), float(x["rank"])),
    )
    monotonic_issues = 0
    for prev, curr in zip(sorted_records, sorted_records[1:]):
        if float(curr["score"]) < float(prev["score"]) and int(curr["rank"]) < int(prev["rank"]):
            monotonic_issues += 1
    gaps = 0
    for prev, curr in zip(sorted_records, sorted_records[1:]):
        if float(prev["score"]) - float(curr["score"]) > 5:
            gaps += 1
    return {
        "records": len(records),
        "score_empty": sum(1 for r in records if r.get("score") is None),
        "rank_empty": sum(1 for r in records if r.get("rank") is None),
        "score_range": [min(scores) if scores else None, max(scores) if scores else None],
        "score_duplicates": score_duplicates,
        "rank_monotonic_issues": monotonic_issues,
        "obvious_gaps": gaps,
        "confidence_distribution": dict(Counter(r.get("confidence", "unknown") for r in records)),
        "source_traceable_rate": completion_rate(
            [{"traceable": 1 if source_ok(r) else None} for r in records],
            "traceable",
        ),
    }


def key_to_triplet(name: str) -> tuple[str, str, str]:
    parts = name.split("_")
    if len(parts) >= 3:
        return parts[0], parts[1], parts[2]
    return (parts[0] if parts else "unknown", parts[1] if len(parts) > 1 else "unknown", "unknown")


def build_per_combo_reports(adm_data: dict[str, list[dict]], rank_data: dict[str, list[dict]]) -> dict[str, dict]:
    combos: dict[tuple[str, str, str], dict] = defaultdict(lambda: {"admissions": [], "rank": []})
    for name, records in adm_data.items():
        combo = key_to_triplet(name)
        combos[combo]["admissions"].extend(records)
    for name, records in rank_data.items():
        combo = key_to_triplet(name)
        combos[combo]["rank"].extend(records)

    summary: dict[str, dict] = {}
    for combo, payload in combos.items():
        province, year, subject_type = combo
        adm_metrics = admissions_metrics(payload["admissions"])
        rank_metrics_payload = rank_metrics(payload["rank"])

        ready = (
            adm_metrics["records"] > 0
            and rank_metrics_payload["records"] > 0
            and (1 - adm_metrics["min_score_empty"] / max(adm_metrics["records"], 1)) >= 0.8
            and (1 - adm_metrics["min_rank_empty"] / max(adm_metrics["records"], 1)) >= 0.7
            and (1 - rank_metrics_payload["score_empty"] / max(rank_metrics_payload["records"], 1)) >= 0.95
            and (1 - rank_metrics_payload["rank_empty"] / max(rank_metrics_payload["records"], 1)) >= 0.95
            and adm_metrics["source_traceable_rate"] >= 0.9
            and rank_metrics_payload["source_traceable_rate"] >= 0.9
            and adm_metrics["abnormal_scores"] == 0
            and rank_metrics_payload["rank_monotonic_issues"] == 0
        )
        blocking = []
        if adm_metrics["records"] == 0:
            blocking.append("missing admissions normalized data")
        if rank_metrics_payload["records"] == 0:
            blocking.append("missing rank table normalized data")
        if adm_metrics["records"] and (1 - adm_metrics["min_score_empty"] / adm_metrics["records"]) < 0.8:
            blocking.append("admissions min_score completeness below 80%")
        if adm_metrics["records"] and (1 - adm_metrics["min_rank_empty"] / adm_metrics["records"]) < 0.7:
            blocking.append("admissions min_rank completeness below 70%")
        if rank_metrics_payload["records"] and (1 - rank_metrics_payload["score_empty"] / rank_metrics_payload["records"]) < 0.95:
            blocking.append("rank table score completeness below 95%")
        if rank_metrics_payload["records"] and (1 - rank_metrics_payload["rank_empty"] / rank_metrics_payload["records"]) < 0.95:
            blocking.append("rank table rank completeness below 95%")
        if adm_metrics["source_traceable_rate"] < 0.9 or rank_metrics_payload["source_traceable_rate"] < 0.9:
            blocking.append("source traceability below 90%")
        if rank_metrics_payload["rank_monotonic_issues"] > 0:
            blocking.append("rank monotonicity issues detected")

        report_path = REPORT_DIR / f"{province}_{year}_{subject_type}_validation.md"
        md = "\n".join(
            [
                f"# {province} {year} {subject_type} Validation",
                "",
                f"- Generated: {iso_now()}",
                f"- Admissions records: {adm_metrics['records']}",
                f"- Rank table records: {rank_metrics_payload['records']}",
                f"- Ready for score lookup demo: {'yes' if ready else 'no'}",
                "",
                "## Admissions",
                f"- school_name empty: {adm_metrics['school_name_empty']}",
                f"- min_score empty: {adm_metrics['min_score_empty']}",
                f"- min_rank empty: {adm_metrics['min_rank_empty']}",
                f"- min_score range: {adm_metrics['min_score_range']}",
                f"- min_rank range: {adm_metrics['min_rank_range']}",
                f"- duplicates: {adm_metrics['duplicates']}",
                f"- abnormal_scores: {adm_metrics['abnormal_scores']}",
                f"- abnormal_ranks: {adm_metrics['abnormal_ranks']}",
                f"- confidence_distribution: {adm_metrics['confidence_distribution']}",
                f"- source_traceable_rate: {adm_metrics['source_traceable_rate']:.2%}",
                "",
                "## Rank Tables",
                f"- score empty: {rank_metrics_payload['score_empty']}",
                f"- rank empty: {rank_metrics_payload['rank_empty']}",
                f"- score range: {rank_metrics_payload['score_range']}",
                f"- score_duplicates: {rank_metrics_payload['score_duplicates']}",
                f"- rank_monotonic_issues: {rank_metrics_payload['rank_monotonic_issues']}",
                f"- obvious_gaps: {rank_metrics_payload['obvious_gaps']}",
                f"- confidence_distribution: {rank_metrics_payload['confidence_distribution']}",
                f"- source_traceable_rate: {rank_metrics_payload['source_traceable_rate']:.2%}",
                "",
                "## Blocking Issues",
                *([f"- {issue}" for issue in blocking] or ["- None"]),
            ]
        )
        write_markdown(report_path, md)

        summary_key = f"{province}_{year}_{subject_type}"
        summary[summary_key] = {
            "province": province,
            "year": year,
            "subject_type": subject_type,
            "admissions_records": adm_metrics["records"],
            "rank_table_records": rank_metrics_payload["records"],
            "admissions_min_score_complete_rate": 1 - adm_metrics["min_score_empty"] / max(adm_metrics["records"], 1),
            "admissions_min_rank_complete_rate": 1 - adm_metrics["min_rank_empty"] / max(adm_metrics["records"], 1),
            "rank_table_score_complete_rate": 1 - rank_metrics_payload["score_empty"] / max(rank_metrics_payload["records"], 1),
            "rank_table_rank_complete_rate": 1 - rank_metrics_payload["rank_empty"] / max(rank_metrics_payload["records"], 1),
            "confidence_high_rate": adm_metrics["confidence_distribution"].get("high", 0) / max(adm_metrics["records"], 1),
            "has_admissions": adm_metrics["records"] > 0,
            "has_rank_table": rank_metrics_payload["records"] > 0,
            "ready_for_score_lookup_demo": ready,
            "ready_reason": "meets minimum thresholds" if ready else "not ready",
            "blocking_issues": blocking,
            "admissions_source_traceable_rate": adm_metrics["source_traceable_rate"],
            "rank_table_source_traceable_rate": rank_metrics_payload["source_traceable_rate"],
        }
    return summary


def build_national_report(adm_data: dict[str, list[dict]], rank_data: dict[str, list[dict]], readiness: dict[str, dict]) -> None:
    admissions_records = [record for records in adm_data.values() for record in records]
    rank_records = [record for records in rank_data.values() for record in records]
    province_counter = Counter(r.get("province", "") for r in admissions_records)
    year_counter = Counter(str(r.get("year", "")) for r in admissions_records)
    subject_counter = Counter(r.get("subject_type", "") for r in admissions_records)
    ready_rows = sorted(
        [value for value in readiness.values() if value["ready_for_score_lookup_demo"]],
        key=lambda x: (-x["admissions_records"], -x["rank_table_records"], x["province"]),
    )

    md = "\n".join(
        [
            "# National Data Quality Report",
            "",
            f"- Generated: {iso_now()}",
            f"- admissions total records: {len(admissions_records)}",
            f"- rank_table total records: {len(rank_records)}",
            "",
            "## Admissions By Province",
            markdown_table(summarize_counter(province_counter), ["key", "count"]),
            "",
            "## Admissions By Year",
            markdown_table(summarize_counter(year_counter), ["key", "count"]),
            "",
            "## Admissions By Subject Type",
            markdown_table(summarize_counter(subject_counter), ["key", "count"]),
            "",
            "## Frontend Ready Provinces",
            markdown_table(ready_rows[:20], ["province", "year", "subject_type", "admissions_records", "rank_table_records", "ready_reason"]),
        ]
    )
    write_markdown(Path("docs") / "national_data_quality_report.md", md)


def main() -> None:
    adm_data = load_normalized(ADMISSIONS_DIR)
    rank_data = load_normalized(RANK_DIR)
    readiness = build_per_combo_reports(adm_data, rank_data)
    dump_json(DATA_WORK / "national_validation_reports" / "readiness_summary.json", readiness)
    build_national_report(adm_data, rank_data, readiness)
    print(f"Validated {len(adm_data)} admissions files and {len(rank_data)} rank files")


if __name__ == "__main__":
    main()

