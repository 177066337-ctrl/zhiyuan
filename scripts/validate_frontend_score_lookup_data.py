from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_DATA = ROOT / "app" / "public" / "data" / "score-lookup"


def main() -> None:
    index = json.loads((APP_DATA / "index.json").read_text(encoding="utf-8"))
    datasets = index["datasets"]
    admissions_files = list((APP_DATA / "admissions").glob("*.json"))
    rank_files = list((APP_DATA / "rank-tables").glob("*.json"))
    max_size = max((path.stat().st_size for path in APP_DATA.rglob("*.json")), default=0)
    total_size = sum(path.stat().st_size for path in APP_DATA.rglob("*.json"))
    print("datasets", len(datasets))
    print("enabled", sum(1 for item in datasets if item["enabled"]))
    print("admissions_files", len(admissions_files))
    print("rank_files", len(rank_files))
    print("max_size_mb", round(max_size / 1024 / 1024, 2))
    print("total_size_mb", round(total_size / 1024 / 1024, 2))


if __name__ == "__main__":
    main()

