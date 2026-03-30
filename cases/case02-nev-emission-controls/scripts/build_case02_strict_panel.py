#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建 Case02 严格口径面板（真实直采优先）：
- 交通碳排放：CEADs 30省分部门清单直接提取（2012-2022）
- 控制变量：NBS 分省年度指标（已有 nbs_*.csv）
- 新能源汽车保有量：严格口径下暂留空（待补官方统一源）
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import sys

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "cases" / "case02-nev-emission-controls" / "data"
sys.path.insert(0, str(ROOT / "tools"))
from province_mapper import get_all_provinces, normalize  # noqa: E402


def main() -> None:
    provinces = get_all_provinces("full")
    years = list(range(2012, 2024))
    panel = pd.MultiIndex.from_product([provinces, years], names=["province", "year"]).to_frame(index=False)

    # NBS base vars
    base_vars = [
        "gdp_100m_cny",
        "tertiary_value_added_100m_cny",
        "resident_population_10k_person",
        "urban_population_10k_person",
        "passenger_turnover_100m_pkm",
        "freight_turnover_100m_tkm",
        "road_mileage_10k_km",
    ]
    for name in base_vars:
        f = DATA_DIR / f"nbs_{name}.csv"
        if not f.exists():
            raise FileNotFoundError(f"缺少NBS文件: {f}")
        df = pd.read_csv(f)
        df["province"] = df["province"].map(lambda x: normalize(str(x), "full"))
        panel = panel.merge(df[["province", "year", name]], on=["province", "year"], how="left")

    # Derived controls
    panel["gdp_per_capita_yuan"] = panel["gdp_100m_cny"] * 10000 / panel["resident_population_10k_person"]
    panel["urbanization_rate"] = panel["urban_population_10k_person"] / panel["resident_population_10k_person"]
    panel["tertiary_share"] = panel["tertiary_value_added_100m_cny"] / panel["gdp_100m_cny"]

    # Direct transport CO2 from CEADs
    co2_file = DATA_DIR / "raw_ceads_sectoral_30prov" / "ceads_transport_co2_direct_30prov_2012_2022.csv"
    if not co2_file.exists():
        raise FileNotFoundError(f"缺少CEADs提取结果: {co2_file}")
    co2 = pd.read_csv(co2_file)
    co2["province"] = co2["province"].map(lambda x: normalize(str(x), "full"))
    panel = panel.merge(co2[["province", "year", "transport_co2_10k_ton_direct"]], on=["province", "year"], how="left")

    # Strict NEV placeholder
    panel["nev_stock_10k"] = pd.NA

    keep_cols = [
        "province",
        "year",
        "transport_co2_10k_ton_direct",
        "nev_stock_10k",
        "gdp_per_capita_yuan",
        "urbanization_rate",
        "passenger_turnover_100m_pkm",
        "freight_turnover_100m_tkm",
        "road_mileage_10k_km",
        "tertiary_share",
        "gdp_100m_cny",
        "tertiary_value_added_100m_cny",
        "resident_population_10k_person",
        "urban_population_10k_person",
    ]
    panel = panel[keep_cols].sort_values(["province", "year"]).reset_index(drop=True)

    out = DATA_DIR / "panel_case02_strict_30prov_2012_2023.csv"
    panel.to_csv(out, index=False, encoding="utf-8-sig")
    print(f"[OK] {out} rows={len(panel)}")
    print("coverage:")
    for c in [
        "transport_co2_10k_ton_direct",
        "nev_stock_10k",
        "gdp_per_capita_yuan",
        "urbanization_rate",
        "passenger_turnover_100m_pkm",
        "freight_turnover_100m_tkm",
        "road_mileage_10k_km",
        "tertiary_share",
    ]:
        print(f"  - {c}: {panel[c].notna().sum()}/{len(panel)}")


if __name__ == "__main__":
    main()

