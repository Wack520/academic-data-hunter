"""
覆盖率计算 — 按年份计算缺失省份
"""

from __future__ import annotations

from collections import defaultdict

from tools.province_mapper import PROVINCE_MAP, normalize


def compute_missing(rows: list[dict], years: list[int], value_col: str) -> dict[int, list[str]]:
    """计算每个年份缺失的省份列表。

    Args:
        rows: 数据行（需包含 province、year 和 value_col 列）
        years: 目标年份列表
        value_col: 数值列名

    Returns:
        dict mapping year -> list of missing province short names
    """
    provinces = list(PROVINCE_MAP.keys())  # 30省短名
    covered_by_year: dict[int, set[str]] = defaultdict(set)

    for r in rows:
        try:
            year = int((r.get("year") or "").strip())
        except ValueError:
            continue
        if year not in years:
            continue

        value = (r.get(value_col) or "").strip()
        if not value:
            continue

        prov_raw = (r.get("province") or "").strip()
        if not prov_raw:
            continue
        try:
            prov = normalize(prov_raw, "short")
        except ValueError:
            continue
        covered_by_year[year].add(prov)

    missing_by_year: dict[int, list[str]] = {}
    for y in years:
        missing = [p for p in provinces if p not in covered_by_year[y]]
        missing_by_year[y] = missing
    return missing_by_year
