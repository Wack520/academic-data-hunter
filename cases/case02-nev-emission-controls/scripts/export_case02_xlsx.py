#!/usr/bin/env python3
"""
导出 case02 的 xlsx 文件（面板 + 来源台账）。
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    data_dir = root / "cases" / "case02-nev-emission-controls" / "data"

    panel_csv = data_dir / "panel_case02_30prov_2012_2023.csv"
    registry_csv = data_dir / "source_registry.csv"
    panel_xlsx = data_dir / "panel_case02_30prov_2012_2023.xlsx"
    registry_xlsx = data_dir / "source_registry.xlsx"

    if not panel_csv.exists():
        raise FileNotFoundError(panel_csv)
    if not registry_csv.exists():
        raise FileNotFoundError(registry_csv)

    pd.read_csv(panel_csv).to_excel(panel_xlsx, index=False)
    pd.read_csv(registry_csv).to_excel(registry_xlsx, index=False)

    print(f"[OK] {panel_xlsx}")
    print(f"[OK] {registry_xlsx}")


if __name__ == "__main__":
    main()
