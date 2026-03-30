#!/usr/bin/env python3
"""
将 case03 的严格部分面板同步回主面板（仅更新 2024 年）。
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CASE_DIR = ROOT / "cases" / "case03-population-10y"
DATA_DIR = CASE_DIR / "data"

MAIN_PANEL = DATA_DIR / "population_by_province.csv"
STRICT_PANEL = DATA_DIR / "population_by_province_strict_partial.csv"
MAIN_REG = DATA_DIR / "source_registry.csv"
STRICT_REG = DATA_DIR / "source_registry_strict_partial.csv"


def load_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def save_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    main_panel = load_csv(MAIN_PANEL)
    strict_panel = load_csv(STRICT_PANEL)
    main_reg = load_csv(MAIN_REG)
    strict_reg = load_csv(STRICT_REG)

    strict_map = {(r["province"], r["year"]): r for r in strict_panel}
    updated = 0
    for r in main_panel:
        if (r.get("year") or "").strip() != "2024":
            continue
        k = (r["province"], "2024")
        src = strict_map.get(k)
        if not src:
            continue
        if not (src.get("resident_population_10k_person") or "").strip():
            continue
        updated += 1
        for col in [
            "resident_population_10k_person",
            "source_id",
            "source_level",
            "source_name",
            "source_url",
            "publish_date",
            "access_date",
            "evidence",
            "note",
        ]:
            r[col] = src.get(col, "")

    # 按主面板中实际用到的source_id裁剪/补齐台账
    used_ids = {r.get("source_id", "").strip() for r in main_panel if (r.get("source_id") or "").strip()}
    strict_map_reg = {r.get("source_id", ""): r for r in strict_reg}
    out_reg = []
    for sid in sorted(used_ids):
        row = strict_map_reg.get(sid)
        if row:
            out_reg.append(row)
    if not out_reg:
        # 兜底，至少保留原台账
        out_reg = main_reg

    save_csv(
        MAIN_PANEL,
        main_panel,
        [
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
    save_csv(
        MAIN_REG,
        out_reg,
        [
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

    print(f"[OK] updated_2024_rows={updated}")
    print(f"[OK] main_panel={MAIN_PANEL}")
    print(f"[OK] main_registry={MAIN_REG} rows={len(out_reg)}")


if __name__ == "__main__":
    main()
