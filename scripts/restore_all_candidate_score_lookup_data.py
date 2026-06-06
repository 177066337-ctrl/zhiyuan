from __future__ import annotations

import shutil
from pathlib import Path

from national_extraction_common import ROOT, iso_now, write_markdown

APP_BASE = ROOT / "app" / "public" / "data" / "score-lookup"
ADMISSIONS_DIR = APP_BASE / "admissions"
RANK_DIR = APP_BASE / "rank-tables"
ARCHIVE_BASE = ROOT / "data_work" / "frontend_score_lookup_archive"
ARCHIVE_ADMISSIONS = ARCHIVE_BASE / "admissions"
ARCHIVE_RANKS = ARCHIVE_BASE / "rank-tables"
RESTORE_REPORT = ROOT / "docs" / "frontend_data_size_report.md"


def copy_tree(source_dir: Path, target_dir: Path) -> int:
    copied = 0
    target_dir.mkdir(parents=True, exist_ok=True)
    if not source_dir.exists():
        return copied
    for path in source_dir.rglob("*.json"):
        relative = path.relative_to(source_dir)
        target = target_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        copied += 1
    return copied


def total_size(folder: Path) -> int:
    return sum(path.stat().st_size for path in folder.rglob("*.json") if path.is_file())


def main() -> None:
    APP_BASE.mkdir(parents=True, exist_ok=True)
    ADMISSIONS_DIR.mkdir(parents=True, exist_ok=True)
    RANK_DIR.mkdir(parents=True, exist_ok=True)

    admissions_before = len(list(ADMISSIONS_DIR.glob("*.json")))
    ranks_before = len(list(RANK_DIR.glob("*.json")))
    size_before = total_size(APP_BASE)

    copied_admissions = copy_tree(ARCHIVE_ADMISSIONS, ADMISSIONS_DIR)
    copied_ranks = copy_tree(ARCHIVE_RANKS, RANK_DIR)

    admissions_after = len(list(ADMISSIONS_DIR.glob("*.json")))
    ranks_after = len(list(RANK_DIR.glob("*.json")))
    size_after = total_size(APP_BASE)

    lines = [
        "# Frontend Data Size Report",
        "",
        f"- 恢复时间：{iso_now()}",
        f"- 恢复前前端数据体积：{size_before / 1024 / 1024:.2f} MB",
        f"- 恢复后前端数据体积：{size_after / 1024 / 1024:.2f} MB",
        f"- 恢复前 admissions 文件数：{admissions_before}",
        f"- 恢复后 admissions 文件数：{admissions_after}",
        f"- 恢复前 rank_table 文件数：{ranks_before}",
        f"- 恢复后 rank_table 文件数：{ranks_after}",
        f"- 从归档恢复 admissions 文件数：{copied_admissions}",
        f"- 从归档恢复 rank_table 文件数：{copied_ranks}",
    ]
    write_markdown(RESTORE_REPORT, "\n".join(lines))
    print(
        f"restored candidate score-lookup data: admissions +{copied_admissions}, "
        f"rank-tables +{copied_ranks}"
    )


if __name__ == "__main__":
    main()
