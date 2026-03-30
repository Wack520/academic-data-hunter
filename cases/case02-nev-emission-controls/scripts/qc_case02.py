#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Case02 一键 QC：
- 主键唯一
- 核心变量覆盖率检查
- 交通碳排放估算值非负
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd


CORE_COLS = [
    "transport_co2_est_10k_ton",
    "nev_stock_10k",
    "gdp_per_capita_yuan",
    "urbanization_rate",
    "passenger_turnover_100m_pkm",
    "freight_turnover_100m_tkm",
    "road_mileage_10k_km",
    "tertiary_share",
]


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    panel = root / "cases" / "case02-nev-emission-controls" / "data" / "panel_case02_30prov_2012_2023.csv"
    if not panel.exists():
        raise FileNotFoundError(panel)

    df = pd.read_csv(panel)
    print(f"文件: {panel}")
    print(f"shape: {df.shape}")

    failed = False

    # 1) 主键唯一
    dup = df.duplicated(subset=["province", "year"]).sum()
    if dup:
        failed = True
        print(f"[失败] 主键重复: {dup}")
    else:
        print("[通过] 主键唯一")

    # 2) 覆盖率
    total = len(df)
    for c in CORE_COLS:
        if c not in df.columns:
            failed = True
            print(f"[失败] 缺少列: {c}")
            continue
        non_na = int(df[c].notna().sum())
        pct = non_na / total * 100 if total else 0
        if pct < 95:
            failed = True
            print(f"[失败] 覆盖率不足: {c} {non_na}/{total} ({pct:.1f}%)")
        else:
            print(f"[通过] 覆盖率: {c} {non_na}/{total} ({pct:.1f}%)")

    # 3) 非负性
    if "transport_co2_est_10k_ton" in df.columns:
        neg = int((pd.to_numeric(df["transport_co2_est_10k_ton"], errors="coerce") < 0).sum())
        if neg:
            failed = True
            print(f"[失败] transport_co2_est_10k_ton 存在负值: {neg} 条")
        else:
            print("[通过] transport_co2_est_10k_ton 非负")

    if failed:
        sys.exit(1)
    print("Case02 QC 全部通过。")


if __name__ == "__main__":
    main()

