"""
生成“下一轮数据补缺任务”文档（供 Codex / 其他 Agent 直接执行）。

示例：
python scripts/run_round.py \
  --data cases/case01-nev-carbon/data/charging_piles_by_province.csv \
  --value-col public_charging_piles \
  --keyword-name 公共充电桩 \
  --year-start 2017 \
  --year-end 2023 \
  --top-years 2 \
  --output cases/case01-nev-carbon/next-round-task.md
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import logging
import os
import sys
from collections import defaultdict


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from tools.province_mapper import PROVINCE_MAP, normalize  # noqa: E402


def load_csv(path: str) -> list[dict]:
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def parse_years(year_start: int, year_end: int) -> list[int]:
    if year_start > year_end:
        raise ValueError("year-start 不能大于 year-end")
    return list(range(year_start, year_end + 1))


def compute_missing(rows: list[dict], years: list[int], value_col: str) -> dict[int, list[str]]:
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


def render_keyword_template(template: str, year: int, keyword_name: str, value_col: str) -> str:
    """
    关键词模板变量：
    - {省名}
    - {year} / {YEAR}
    - {keyword_name}
    - {value_col}
    """
    return (
        template.replace("{year}", str(year))
        .replace("{YEAR}", str(year))
        .replace("{keyword_name}", keyword_name)
        .replace("{value_col}", value_col)
    )


def build_markdown(
    data_path: str,
    value_col: str,
    keyword_name: str,
    keyword_templates: list[str],
    missing_by_year: dict[int, list[str]],
    top_years: int,
) -> str:
    today = dt.date.today().isoformat()
    year_stats = []
    for y, missing in missing_by_year.items():
        covered = 30 - len(missing)
        year_stats.append((y, covered, len(missing)))

    # 优先策略：先补缺口最少的年份
    focus = [x for x in sorted(year_stats, key=lambda t: (t[2], t[0])) if x[2] > 0][:top_years]

    lines = []
    lines.append(f"# 下一轮补缺任务（生成日期：{today}）")
    lines.append("")
    lines.append("## 输入数据")
    lines.append(f"- 数据文件：`{data_path}`")
    lines.append(f"- 数值列：`{value_col}`")
    lines.append("")
    lines.append("## 覆盖现状")
    lines.append("")
    lines.append("| 年份 | 已覆盖省份 | 缺失省份 |")
    lines.append("|------|-----------:|---------:|")
    for y, covered, missing_count in sorted(year_stats):
        lines.append(f"| {y} | {covered} | {missing_count} |")

    lines.append("")
    lines.append("## 本轮优先年份（缺口最少优先）")
    if not focus:
        lines.append("- 当前年份范围内已无缺口。")
        return "\n".join(lines) + "\n"

    for y, covered, missing_count in focus:
        lines.append(f"- **{y}年**：缺失 {missing_count} 省（已覆盖 {covered}/30）")

    lines.append("")
    lines.append("## 逐年缺失省份清单")
    for y, _, _ in focus:
        missing = missing_by_year[y]
        lines.append(f"### {y}年")
        lines.append(", ".join(missing))
        lines.append("")
        lines.append("建议关键词模板：")
        lines.append("```")
        for tpl in keyword_templates:
            lines.append(f"\"{render_keyword_template(tpl, y, keyword_name, value_col)}\"")
        lines.append("```")
        lines.append("")

    lines.append("## 执行红线")
    lines.append("- 禁止估算/推算/插值/外推")
    lines.append("- 每条入库值必须有 source_url")
    lines.append("- C级来源需可交叉核验")
    lines.append("- 连续3省搜不到即可停止该年份")
    lines.append("")
    lines.append("## 本轮产出要求")
    lines.append("- 更新数据CSV")
    lines.append("- 更新 source_registry.csv")
    lines.append("- 更新 progress-report.md（覆盖变化 + 未入库原因）")
    lines.append("")
    return "\n".join(lines)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    parser = argparse.ArgumentParser(description="生成下一轮补缺任务文档")
    parser.add_argument("--data", required=True, help="输入CSV")
    parser.add_argument("--value-col", required=True, help="数值列名")
    parser.add_argument("--year-start", type=int, required=True, help="起始年份")
    parser.add_argument("--year-end", type=int, required=True, help="结束年份")
    parser.add_argument("--top-years", type=int, default=2, help="优先年份数量（默认2）")
    parser.add_argument("--keyword-name", default=None, help="搜索关键词中的指标名（默认使用 value-col）")
    parser.add_argument(
        "--keyword-template1",
        default="{省名} {keyword_name} {year} 保有量 台",
        help="关键词模板1（支持 {省名}/{year}/{keyword_name}/{value_col}）",
    )
    parser.add_argument(
        "--keyword-template2",
        default="{省名} {keyword_name} {year} 截至 台",
        help="关键词模板2（可传空字符串关闭）",
    )
    parser.add_argument("--output", required=True, help="输出md文件路径")
    args = parser.parse_args()

    rows = load_csv(args.data)
    years = parse_years(args.year_start, args.year_end)
    missing_by_year = compute_missing(rows, years, args.value_col)
    keyword_name = args.keyword_name or args.value_col
    keyword_templates = [x for x in [args.keyword_template1, args.keyword_template2] if (x or "").strip()]
    md = build_markdown(
        args.data,
        args.value_col,
        keyword_name,
        keyword_templates,
        missing_by_year,
        args.top_years,
    )

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(md)

    logging.info("已生成: %s", args.output)
    logging.info("输入行数: %s", len(rows))


if __name__ == "__main__":
    main()
