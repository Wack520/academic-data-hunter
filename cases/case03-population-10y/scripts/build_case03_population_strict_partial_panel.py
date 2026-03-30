#!/usr/bin/env python3
"""
将 case03 的 2024 年短名单回填到“严格部分面板”（不覆盖主面板）。
"""

from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[3]
CASE_DIR = ROOT / "cases" / "case03-population-10y"
DATA_DIR = CASE_DIR / "data"

SHORTLIST_PATH = DATA_DIR / "population_2024_shortlist_review.csv"
PANEL_PATH = DATA_DIR / "population_by_province.csv"
BASE_REG_PATH = DATA_DIR / "source_registry.csv"
OUT_PANEL_PATH = DATA_DIR / "population_by_province_strict_partial.csv"
OUT_REG_PATH = DATA_DIR / "source_registry_strict_partial.csv"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="构建 case03 严格部分面板（2024）")
    p.add_argument("--shortlist", default=str(SHORTLIST_PATH))
    p.add_argument("--panel", default=str(PANEL_PATH))
    p.add_argument("--base-registry", default=str(BASE_REG_PATH))
    p.add_argument("--output-panel", default=str(OUT_PANEL_PATH))
    p.add_argument("--output-registry", default=str(OUT_REG_PATH))
    p.add_argument("--tag-note", default="短名单自动回填（待人工二审）")
    return p.parse_args()


def norm_level(s: str) -> str:
    s = (s or "").strip().upper()
    if s.startswith("A"):
        return "A"
    if s.startswith("B"):
        return "B"
    if s.startswith("C"):
        return "C"
    return "B"


def source_name_from_url(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    if not host:
        return "省级政府站点（2024人口发布）"
    return f"{host}（2024人口发布）"


def load_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    args = parse_args()
    shortlist = load_csv(Path(args.shortlist))
    panel = load_csv(Path(args.panel))
    base_registry = load_csv(Path(args.base_registry))

    today = date.today().isoformat()
    fill_map = {(r["province"], "2024"): r for r in shortlist}

    source_rows: list[dict] = []
    source_id_map: dict[tuple[str, str], str] = {}
    for idx, r in enumerate(shortlist, start=1):
        sid = f"SRC_CASE03_POP2024_SHORT_{idx:02d}"
        key = (r["province"], "2024")
        source_id_map[key] = sid
        source_rows.append(
            {
                "source_id": sid,
                "variable": "resident_population_10k_person",
                "source_level": norm_level(r.get("source_level_suggest", "")),
                "source_name": source_name_from_url(r.get("source_url", "")),
                "source_url": r.get("source_url", ""),
                "cross_check_url": "",
                "publish_date": "",
                "access_date": today,
                "evidence_file": "population_2024_shortlist_review.csv",
                "is_primary": "0",
                "note": f"{args.tag_note}; confidence={r.get('confidence', '')}; query={r.get('search_query', '')}",
            }
        )

    updated = 0
    for row in panel:
        key = ((row.get("province") or "").strip(), (row.get("year") or "").strip())
        cand = fill_map.get(key)
        if not cand:
            continue
        updated += 1
        row["resident_population_10k_person"] = cand["resident_population_10k_person"]
        row["source_id"] = source_id_map[key]
        row["source_level"] = norm_level(cand.get("source_level_suggest", "B"))
        row["source_name"] = source_name_from_url(cand.get("source_url", ""))
        row["source_url"] = cand.get("source_url", "")
        row["publish_date"] = ""
        row["access_date"] = today
        row["evidence"] = (cand.get("evidence_sentence") or "")[:500]
        row["note"] = args.tag_note

    fieldnames = [
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
    ]
    write_csv(Path(args.output_panel), panel, fieldnames)
    merged = list(base_registry)
    existing = {r.get("source_id", "") for r in merged}
    for r in source_rows:
        if r["source_id"] not in existing:
            merged.append(r)
            existing.add(r["source_id"])
    write_csv(
        Path(args.output_registry),
        merged,
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

    print(f"[OK] updated rows (2024 shortlist): {updated}")
    print(f"[OK] panel => {args.output_panel}")
    print(f"[OK] registry => {args.output_registry}")


if __name__ == "__main__":
    main()
