"""
Reference Fill Agent

用途：作为 run_auto_rounds 的 --agent-cmd 执行器，
根据任务文件中的年份清单，从 reference CSV 回填 data CSV 的缺失值。

示例：
python tools/agent_ref_fill.py \
  --task cases/case01-nev-carbon/next-round-task.md \
  --data cases/case01-nev-carbon/tmp/panel_seed.csv \
  --reference "d:\\Desk\\app\\math\\交付数据_30省面板_2012_2023\\panel_30prov_2012_2023.csv" \
  --value-col public_charging_piles \
  --key province,year
"""

from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path

from tools.io import load_csv, save_csv


def parse_task_years(task_file: Path) -> set[str]:
    txt = task_file.read_text(encoding="utf-8")
    years = set(re.findall(r"^###\s*(\d{4})年", txt, flags=re.MULTILINE))
    return years


def make_key(row: dict, key_cols: list[str]) -> tuple:
    return tuple((row.get(k) or "").strip() for k in key_cols)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    parser = argparse.ArgumentParser(description="Reference Fill Agent")
    parser.add_argument("--task", required=True, help="任务文件")
    parser.add_argument("--data", required=True, help="待回填CSV")
    parser.add_argument("--reference", required=True, help="参考CSV")
    parser.add_argument("--value-col", required=True, help="回填目标列")
    parser.add_argument("--key", default="province,year", help="主键列")
    args = parser.parse_args()

    task_file = Path(args.task)
    data_file = Path(args.data)
    ref_file = Path(args.reference)
    key_cols = [x.strip() for x in args.key.split(",") if x.strip()]

    years = parse_task_years(task_file)
    data_rows = load_csv(data_file)
    ref_rows = load_csv(ref_file)
    if not data_rows or not ref_rows:
        logging.warning("empty input, skip")
        return

    ref_idx = {make_key(r, key_cols): r for r in ref_rows}
    filled = 0
    scanned = 0

    for r in data_rows:
        y = (r.get("year") or "").strip()
        if years and y not in years:
            continue
        scanned += 1
        cur = (r.get(args.value_col) or "").strip()
        if cur:
            continue
        k = make_key(r, key_cols)
        rr = ref_idx.get(k)
        if not rr:
            continue
        rv = (rr.get(args.value_col) or "").strip()
        if not rv:
            continue
        r[args.value_col] = rv
        filled += 1

    fieldnames = list(data_rows[0].keys())
    save_csv(data_rows, data_file, fieldnames)
    logging.info("task years=%s", sorted(years) if years else "ALL")
    logging.info("scanned=%s, filled=%s, value_col=%s", scanned, filled, args.value_col)


if __name__ == "__main__":
    main()
