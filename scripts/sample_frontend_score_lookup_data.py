from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_DATA = ROOT / "app" / "public" / "data" / "score-lookup"


def main() -> None:
    index = json.loads((APP_DATA / "index.json").read_text(encoding="utf-8"))
    enabled = [item for item in index["datasets"] if item["enabled"]]
    for item in enabled[:10]:
        print(json.dumps(item, ensure_ascii=False))


if __name__ == "__main__":
    main()
