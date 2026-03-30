"""
面板数据合并工具
用法: python panel_merger.py --base panel.csv --new data.csv --on province,year --map-province short-to-full
"""

from __future__ import annotations

import argparse
import contextlib
import logging
from typing import Literal, TypeAlias, cast

from tools.io import load_csv, save_csv
from tools.province_mapper import normalize

Row: TypeAlias = dict[str, str]
PanelKey: TypeAlias = tuple[str, ...]
ProvinceMapTarget: TypeAlias = Literal["short", "full"]


def merge_panel(
    base_rows: list[Row],
    new_rows: list[Row],
    key_cols: list[str],
    new_cols: list[str],
    province_target: ProvinceMapTarget | None = None,
) -> tuple[list[Row], int]:
    """左连接合并"""
    # 建立新数据索引
    new_index: dict[PanelKey, Row] = {}
    for r in new_rows:
        prov = r.get("province", "")
        if province_target:
            with contextlib.suppress(ValueError):
                prov = normalize(prov, province_target)
        new_key: PanelKey = tuple(prov if k == "province" else r.get(k, "") for k in key_cols)
        new_index[new_key] = r

    # 合并
    merged = 0
    for r in base_rows:
        base_key: PanelKey = tuple(r.get(k, "") for k in key_cols)
        match = new_index.get(base_key)
        if match:
            for col in new_cols:
                if col in match and match[col].strip():
                    r[col] = match[col]
                    merged += 1

    return base_rows, merged


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    parser = argparse.ArgumentParser(description="面板数据合并工具")
    parser.add_argument("--base", required=True, help="基础面板CSV")
    parser.add_argument("--new", required=True, help="新数据CSV")
    parser.add_argument("--on", default="province,year", help="连接键")
    parser.add_argument("--cols", default=None, help="要合并的列(逗号分隔,默认取new中非键列)")
    parser.add_argument("--map-province", default=None, choices=["short", "full"], help="省份名映射目标格式")
    parser.add_argument("--output", default=None, help="输出文件(默认覆盖base)")
    args = parser.parse_args()

    base = load_csv(args.base)
    new = load_csv(args.new)
    key_cols = [k.strip() for k in args.on.split(",")]

    new_cols = [k.strip() for k in args.cols.split(",")] if args.cols else [k for k in new[0] if k not in key_cols]

    logging.info("基础面板: %s 行", len(base))
    logging.info("新数据: %s 行, 合并列: %s", len(new), new_cols)

    # 为base添加新列（如不存在）
    for col in new_cols:
        for r in base:
            if col not in r:
                r[col] = ""

    province_target = cast(ProvinceMapTarget | None, args.map_province)
    base, merged = merge_panel(base, new, key_cols, new_cols, province_target)

    fieldnames = list(base[0].keys())
    output = args.output or args.base
    save_csv(base, output, fieldnames)

    logging.info("合并完成: %s 个值已填入", merged)
    logging.info("输出: %s", output)

    # 统计
    for col in new_cols:
        non_empty = sum(1 for r in base if r.get(col, "").strip())
        logging.info("%s: %s/%s 非空", col, non_empty, len(base))


if __name__ == "__main__":
    main()
