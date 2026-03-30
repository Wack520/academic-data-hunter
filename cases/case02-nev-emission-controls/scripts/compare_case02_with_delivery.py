#!/usr/bin/env python3
"""
对比 case02 输出 与 math/交付数据_30省面板_2012_2023 的差异，并产出 markdown 报告。
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def main() -> None:
    root = Path(__file__).resolve().parents[3]
    case02_panel = root / "cases" / "case02-nev-emission-controls" / "data" / "panel_case02_30prov_2012_2023.csv"
    delivery_panel = root.parent / "math" / "交付数据_30省面板_2012_2023" / "panel_30prov_2012_2023.csv"
    out_md = root / "cases" / "case02-nev-emission-controls" / "comparison_with_delivery.md"

    if not case02_panel.exists():
        raise FileNotFoundError(case02_panel)
    if not delivery_panel.exists():
        raise FileNotFoundError(delivery_panel)

    a = pd.read_csv(case02_panel)
    b = pd.read_csv(delivery_panel)

    key = ["province", "year"]
    overlap_cols = [c for c in a.columns if c in b.columns and c not in key]
    a_only_cols = [c for c in a.columns if c not in b.columns]
    b_only_cols = [c for c in b.columns if c not in a.columns]

    merged = a.merge(b, on=key, how="inner", suffixes=("_case02", "_delivery"))

    diff_rows = []
    for c in overlap_cols:
        x = pd.to_numeric(merged[f"{c}_case02"], errors="coerce")
        y = pd.to_numeric(merged[f"{c}_delivery"], errors="coerce")
        both = x.notna() & y.notna()
        if both.any():
            abs_diff = (x[both] - y[both]).abs()
            neq = (abs_diff > 1e-9).sum()
            diff_rows.append(
                {
                    "column": c,
                    "both_non_na": int(both.sum()),
                    "unequal_count": int(neq),
                    "max_abs_diff": float(abs_diff.max()),
                    "mean_abs_diff": float(abs_diff.mean()),
                }
            )
        else:
            diff_rows.append(
                {
                    "column": c,
                    "both_non_na": 0,
                    "unequal_count": 0,
                    "max_abs_diff": 0.0,
                    "mean_abs_diff": 0.0,
                }
            )

    diff_df = pd.DataFrame(diff_rows).sort_values("column")

    lines = []
    lines.append("# Case02 与交付面板差异报告")
    lines.append("")
    lines.append(f"- Case02: `{case02_panel}`")
    lines.append(f"- Delivery: `{delivery_panel}`")
    lines.append("")
    lines.append("## 基本信息")
    lines.append(f"- Case02 shape: {a.shape}")
    lines.append(f"- Delivery shape: {b.shape}")
    lines.append(f"- Inner join on (province,year): {merged.shape[0]} 行")
    lines.append("")
    lines.append("## 列集合差异")
    lines.append(f"- 共同列（含键）数量: {len([c for c in a.columns if c in b.columns])}")
    lines.append(f"- 仅 Case02 有: {a_only_cols}")
    lines.append(f"- 仅 Delivery 有: {b_only_cols}")
    lines.append("")
    lines.append("## 共同业务列数值差异")
    if diff_df.empty:
        lines.append("无共同业务列可对比。")
    else:
        lines.append("")
        lines.append("| column | both_non_na | unequal_count | max_abs_diff | mean_abs_diff |")
        lines.append("|---|---:|---:|---:|---:|")
        for _, r in diff_df.iterrows():
            lines.append(
                f"| {r['column']} | {int(r['both_non_na'])} | {int(r['unequal_count'])} | {r['max_abs_diff']:.6f} | {r['mean_abs_diff']:.6f} |"
            )

    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] {out_md}")


if __name__ == "__main__":
    main()
