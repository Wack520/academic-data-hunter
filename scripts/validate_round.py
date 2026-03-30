"""
回合结果校验脚本（QC + 来源台账一致性）

示例：
python scripts/validate_round.py \
  --data cases/case01-nev-carbon/data/charging_piles_by_province.csv \
  --registry cases/case01-nev-carbon/data/source_registry.csv \
  --variable charging \
  --value-col public_charging_piles \
  --check-unit 台
"""

from __future__ import annotations

import argparse
import csv
import logging
import os
import sys
from collections import Counter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.qc_checker import check_required, check_uniqueness, check_unit  # noqa: E402


def load_csv(path: str) -> list[dict]:
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def has_value(row: dict, value_cols: list[str] | None) -> bool:
    if not value_cols:
        return True
    return any(bool((row.get(c) or "").strip()) for c in value_cols)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    parser = argparse.ArgumentParser(description="回合结果校验（QC + registry一致性）")
    parser.add_argument("--data", required=True, help="数据CSV")
    parser.add_argument("--registry", required=True, help="来源台账CSV")
    parser.add_argument("--variable", required=True, help="registry中 variable 值，如 charging")
    parser.add_argument("--key", default="province,year", help="主键列")
    parser.add_argument(
        "--required",
        default="source_url,source_name,source_level,source_id,access_date",
        help="必填列",
    )
    parser.add_argument("--value-col", default=None, help="数值列（有值时才做来源检查）")
    parser.add_argument("--check-unit", default=None, help="期望单位（如 台/辆）")
    parser.add_argument(
        "--strict-c-cross-check",
        action="store_true",
        help="开启后，C级来源缺少 cross_check_url 将判定为失败（默认仅告警）",
    )
    args = parser.parse_args()

    data_rows = load_csv(args.data)
    reg_rows = load_csv(args.registry)
    key_cols = [x.strip() for x in args.key.split(",") if x.strip()]
    required_cols = [x.strip() for x in args.required.split(",") if x.strip()]
    value_cols = [x.strip() for x in (args.value_col or "").split(",") if x.strip()]

    logging.info("数据行数: %s", len(data_rows))
    logging.info("台账行数: %s", len(reg_rows))

    failed = False

    # 1) 主键唯一性
    dupes = check_uniqueness(data_rows, key_cols)
    if dupes:
        failed = True
        logging.error("主键重复: %s 组", len(dupes))
        for k, v in list(dupes.items())[:10]:
            logging.error("  %s: %s次", k, v)
    else:
        logging.info("主键唯一性通过")

    # 2) 必填字段
    req_issues = check_required(data_rows, required_cols, value_cols)
    if req_issues:
        failed = True
        logging.error("必填字段缺失: %s 处", len(req_issues))
        for line, prov, year, col in req_issues[:10]:
            logging.error("  行%s: %s %s 缺少 %s", line, prov, year, col)
    else:
        logging.info("必填字段检查通过")

    # 3) 单位检查（可选）
    if args.check_unit:
        unit_issues = check_unit(data_rows, value_cols, args.check_unit) if value_cols else []
        if unit_issues:
            failed = True
            logging.error("单位检查失败: %s 处", len(unit_issues))
            for line, prov, year, col, raw, reason in unit_issues[:10]:
                logging.error("  行%s: %s %s %s=%r (%s)", line, prov, year, col, raw, reason)
        else:
            logging.info("单位检查通过（%s）", args.check_unit)

    # 4) 台账一致性（source_level + source_name + source_url）
    reg_filtered = [r for r in reg_rows if (r.get("variable") or "").strip() == args.variable]
    reg_key_counter = Counter(
        (
            (r.get("source_level") or "").strip(),
            (r.get("source_name") or "").strip(),
            (r.get("source_url") or "").strip(),
        )
        for r in reg_filtered
    )
    reg_keys = set(reg_key_counter.keys())
    data_missing_in_reg = []
    c_level_no_cross = []

    # source_id 映射（如果数据里有 source_id 字段）
    has_source_id = bool(data_rows and "source_id" in data_rows[0])
    reg_source_ids = {(r.get("source_id") or "").strip() for r in reg_filtered}
    source_id_issues = []

    for idx, r in enumerate(data_rows, start=2):
        if not has_value(r, value_cols):
            continue

        k = (
            (r.get("source_level") or "").strip(),
            (r.get("source_name") or "").strip(),
            (r.get("source_url") or "").strip(),
        )
        if k not in reg_keys:
            data_missing_in_reg.append((idx, r.get("province", "?"), r.get("year", "?"), k))

        if (r.get("source_level") or "").strip() == "C":
            # 找到匹配registry行，判断 cross_check_url
            matched = [
                rr
                for rr in reg_filtered
                if (rr.get("source_level") or "").strip() == k[0]
                and (rr.get("source_name") or "").strip() == k[1]
                and (rr.get("source_url") or "").strip() == k[2]
            ]
            if matched and not any((m.get("cross_check_url") or "").strip() for m in matched):
                c_level_no_cross.append((idx, r.get("province", "?"), r.get("year", "?"), k[1]))

        if has_source_id:
            sid = (r.get("source_id") or "").strip()
            if not sid:
                source_id_issues.append((idx, r.get("province", "?"), r.get("year", "?"), "缺少source_id"))
            elif sid not in reg_source_ids:
                source_id_issues.append(
                    (idx, r.get("province", "?"), r.get("year", "?"), f"source_id未在registry找到: {sid}")
                )

    if data_missing_in_reg:
        failed = True
        logging.error("数据来源未在registry登记: %s 条", len(data_missing_in_reg))
        for item in data_missing_in_reg[:10]:
            line, prov, year, k = item
            logging.error("  行%s: %s %s -> %s", line, prov, year, k)
    else:
        logging.info("数据来源与registry匹配")

    if c_level_no_cross:
        if args.strict_c_cross_check:
            logging.error("C级来源缺少cross_check_url: %s 条", len(c_level_no_cross))
        else:
            logging.warning("C级来源缺少cross_check_url: %s 条", len(c_level_no_cross))
        for item in c_level_no_cross[:10]:
            line, prov, year, source_name = item
            if args.strict_c_cross_check:
                logging.error("  行%s: %s %s -> %s", line, prov, year, source_name)
            else:
                logging.warning("  行%s: %s %s -> %s", line, prov, year, source_name)
        if args.strict_c_cross_check:
            failed = True
    else:
        logging.info("C级来源交叉核验检查通过")

    if has_source_id:
        if source_id_issues:
            failed = True
            logging.error("source_id 对齐问题: %s 条", len(source_id_issues))
            for line, prov, year, reason in source_id_issues[:10]:
                logging.error("  行%s: %s %s -> %s", line, prov, year, reason)
        else:
            logging.info("source_id 对齐检查通过")

    if failed:
        sys.exit(1)
    logging.info("全部检查通过。")


if __name__ == "__main__":
    main()
