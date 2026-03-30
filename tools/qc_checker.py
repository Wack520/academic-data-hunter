"""
QC Checker — 数据质量检查工具
用法:
  python qc_checker.py data.csv --key province,year --required source_url
  python qc_checker.py data.csv --value-col public_charging_piles --check-unit 台
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from collections import Counter
from typing import TypeAlias

from pydantic import ValidationError

from tools.io import load_csv
from tools.models import parse_panel_row

Row: TypeAlias = dict[str, str]
DuplicateKey: TypeAlias = tuple[str, ...]
RequiredIssue: TypeAlias = tuple[int, str, str, str]
UnitIssue: TypeAlias = tuple[int, str, str, str, str, str]
InputIssue: TypeAlias = tuple[int, str]


def check_uniqueness(rows: list[Row], key_cols: list[str]) -> dict[DuplicateKey, int]:
    """检查主键唯一性"""
    keys: list[DuplicateKey] = [tuple((r.get(k) or "") for k in key_cols) for r in rows]
    dupes = {k: v for k, v in Counter(keys).items() if v > 1}
    return dupes


def check_required(
    rows: list[Row], required_cols: list[str], value_cols: list[str] | None = None
) -> list[RequiredIssue]:
    """检查必填字段：当任一 value_cols 有值时，required_cols 不能为空"""
    issues: list[RequiredIssue] = []
    for i, r in enumerate(rows):
        if value_cols:
            has_value = any((r.get(c) or "").strip() for c in value_cols)
            if not has_value:
                continue  # 值为空时不检查来源
        for col in required_cols:
            if not r.get(col, "").strip():
                issues.append((i + 2, r.get("province", "?"), r.get("year", "?"), col))
    return issues


def check_unit(rows: list[Row], value_cols: list[str], expected_unit: str) -> list[UnitIssue]:
    """
    检查单位异常（轻量启发式）：
    - 若值中出现“万/亿”等数量级单位，判定为异常（应先完成换算再入库）
    - 若值中出现明确单位且不包含 expected_unit，判定为异常
    """
    issues: list[UnitIssue] = []
    unit_keywords = ["台", "辆", "吨", "千瓦时", "kwh", "mwh", "gwh"]
    for i, r in enumerate(rows):
        for col in value_cols:
            raw = (r.get(col) or "").strip()
            if not raw:
                continue

            # 纯数字（含小数/负号/科学计数）直接通过
            if re.fullmatch(r"[-+]?\d+(\.\d+)?([eE][-+]?\d+)?", raw):
                continue

            # 出现“万/亿”等一般说明未标准化
            if any(x in raw for x in ["万", "亿"]):
                issues.append((i + 2, r.get("province", "?"), r.get("year", "?"), col, raw, "包含万/亿等未换算单位"))
                continue

            lower_raw = raw.lower()
            found_unit_keyword = any(k in raw or k in lower_raw for k in unit_keywords)
            if found_unit_keyword and expected_unit not in raw:
                issues.append(
                    (i + 2, r.get("province", "?"), r.get("year", "?"), col, raw, f"单位疑似不为{expected_unit}")
                )
    return issues


def validate_input_rows(rows: list[Row]) -> list[InputIssue]:
    issues: list[InputIssue] = []
    for index, row in enumerate(rows, start=2):
        try:
            parse_panel_row(row)
        except ValidationError as exc:
            issues.append((index, str(exc.errors()[0].get("msg", "invalid row"))))
    return issues


def print_coverage(rows: list[Row], cols: list[str]) -> None:
    """打印各列非空统计"""
    total = len(rows)
    logging.info("%s", f"{'列名':<40} {'非空':>6} / {total}  {'覆盖率':>8}")
    logging.info("%s", "-" * 65)
    for col in cols:
        non_empty = sum(1 for r in rows if r.get(col, "").strip())
        pct = non_empty / total * 100 if total else 0
        logging.info("%s", f"{col:<40} {non_empty:>6} / {total}  {pct:>7.1f}%")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    parser = argparse.ArgumentParser(description="数据QC检查工具")
    parser.add_argument("csv_file", help="待检查的CSV文件")
    parser.add_argument("--key", default="province,year", help="主键列名(逗号分隔)")
    parser.add_argument("--required", default="source_url", help="必填列(逗号分隔)")
    parser.add_argument("--value-col", default=None, help="数值列(逗号分隔；仅当任一列有值时检查required)")
    parser.add_argument("--check-unit", default=None, help="期望单位（如 台/辆）；做轻量启发式检查")
    args = parser.parse_args()

    rows = load_csv(args.csv_file)
    key_cols = [k.strip() for k in args.key.split(",")]
    required_cols = [k.strip() for k in args.required.split(",")]
    all_cols = list(rows[0].keys()) if rows else []

    value_cols = [v.strip() for v in (args.value_col or "").split(",") if v.strip()]

    logging.info("文件: %s", args.csv_file)
    logging.info("总行数: %s", len(rows))
    logging.info("列数: %s", len(all_cols))

    input_issues: list[InputIssue] = []
    if {"province", "year"}.issubset(all_cols):
        input_issues = validate_input_rows(rows)
        if input_issues:
            logging.error("输入数据模型校验失败: %s 处", len(input_issues))
            for line, reason in input_issues[:10]:
                logging.error("   行%s: %s", line, reason)
            if len(input_issues) > 10:
                logging.error("   ... 共%s处", len(input_issues))
        else:
            logging.info("输入数据模型校验通过 (PanelRow)")

    # 1. 唯一性检查
    dupes = check_uniqueness(rows, key_cols)
    if dupes:
        logging.error("主键重复 (%s):", ",".join(key_cols))
        for k, v in dupes.items():
            logging.error("   %s: %s次", k, v)
    else:
        logging.info("主键唯一性通过 (%s)", ",".join(key_cols))

    # 2. 必填字段检查
    issues = check_required(rows, required_cols, value_cols)
    if issues:
        logging.error("必填字段缺失 (%s):", ",".join(required_cols))
        for line, prov, year, col in issues[:10]:
            logging.error("   行%s: %s %s 缺少 %s", line, prov, year, col)
        if len(issues) > 10:
            logging.error("   ... 共%s处", len(issues))
    else:
        logging.info("必填字段检查通过")

    # 3. 单位检查（可选）
    unit_issues = []
    if args.check_unit:
        if not value_cols:
            # 自动推断：排除key/来源/备注等字段
            value_cols = [
                c
                for c in all_cols
                if c not in key_cols
                and c not in required_cols
                and not c.endswith("_url")
                and not c.startswith("source_")
                and c != "note"
            ]
            value_cols = value_cols[:2]  # 控制检查范围，避免误报

        if not value_cols:
            logging.warning("跳过单位检查: 未找到可检查数值列")
        else:
            unit_issues = check_unit(rows, value_cols, args.check_unit)
            if unit_issues:
                logging.error("单位检查失败（期望单位: %s）:", args.check_unit)
                for line, prov, year, col, raw, reason in unit_issues[:10]:
                    logging.error("   行%s: %s %s %s=%r (%s)", line, prov, year, col, raw, reason)
                if len(unit_issues) > 10:
                    logging.error("   ... 共%s处", len(unit_issues))
            else:
                logging.info("单位检查通过（期望单位: %s）", args.check_unit)

    # 4. 覆盖率统计
    print_coverage(rows, all_cols)

    # 返回码
    if input_issues or dupes or issues or unit_issues:
        sys.exit(1)


if __name__ == "__main__":
    main()
