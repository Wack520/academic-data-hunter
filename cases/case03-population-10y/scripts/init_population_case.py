#!/usr/bin/env python3
"""
快速初始化“人口数据”案例骨架。
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
from province_mapper import get_all_provinces  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="初始化人口案例骨架")
    p.add_argument("--case-dir", required=True, help="案例目录，如 cases/case03-population-10y")
    p.add_argument("--year-start", type=int, default=2015)
    p.add_argument("--year-end", type=int, default=2024)
    p.add_argument("--overwrite", action="store_true")
    return p.parse_args()


def ensure_write(path: Path, overwrite: bool) -> None:
    if path.exists() and not overwrite:
        raise FileExistsError(f"exists: {path} (use --overwrite)")


def main() -> None:
    args = parse_args()
    if args.year_start > args.year_end:
        raise ValueError("year-start must <= year-end")

    case_dir = (ROOT / args.case_dir).resolve()
    data_dir = case_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    data_csv = data_dir / "population_by_province.csv"
    reg_csv = data_dir / "source_registry.csv"
    task_md = case_dir / "task-spec.md"
    prog_md = case_dir / "progress-report.md"
    log_md = case_dir / "search-log.md"
    readme_md = case_dir / "README.md"

    for p in [data_csv, reg_csv, task_md, prog_md, log_md, readme_md]:
        ensure_write(p, args.overwrite)

    years = list(range(args.year_start, args.year_end + 1))
    provs = get_all_provinces("full")
    rows = []
    for prov in provs:
        for y in years:
            rows.append(
                {
                    "province": prov,
                    "year": y,
                    "resident_population_10k_person": "",
                    "source_id": "",
                    "source_level": "",
                    "source_name": "",
                    "source_url": "",
                    "publish_date": "",
                    "access_date": "",
                    "evidence": "",
                    "note": "",
                }
            )

    with data_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "province",
                "year",
                "resident_population_10k_person",
                "source_id",
                "source_level",
                "source_name",
                "source_url",
                "publish_date",
                "access_date",
                "evidence",
                "note",
            ],
        )
        w.writeheader()
        w.writerows(rows)

    with reg_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "source_id",
                "variable",
                "source_level",
                "source_name",
                "source_url",
                "cross_check_url",
                "publish_date",
                "access_date",
                "evidence_file",
                "is_primary",
                "note",
            ],
        )
        w.writeheader()

    task_md.write_text(
        (
            "# 任务规范：人口数据\n\n"
            f"- 口径：年末常住人口（万人）\n"
            f"- 范围：30省，{args.year_start}-{args.year_end}\n"
            "- 红线：禁止估算/插值，必须有来源URL\n"
        ),
        encoding="utf-8",
    )

    prog_md.write_text(
        (f"# 进度汇报\n\n- 初始化完成：{len(rows)} 行骨架\n- 已填充：0\n"),
        encoding="utf-8",
    )

    log_md.write_text("# 搜索日志\n\n- Round 0：案例初始化完成。\n", encoding="utf-8")
    readme_md.write_text(
        (
            "# 人口数据案例\n\n"
            f"- 规模：30省 × {len(years)}年 = {len(rows)} 行\n"
            "- 数据文件：`data/population_by_province.csv`\n"
        ),
        encoding="utf-8",
    )

    print(f"[DONE] case initialized: {case_dir}")
    print(f"rows={len(rows)} years={args.year_start}-{args.year_end}")


if __name__ == "__main__":
    main()
