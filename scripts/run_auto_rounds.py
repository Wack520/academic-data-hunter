"""
多轮自动调度脚本（任务生成 -> 调用Agent -> 校验 -> 判断是否继续）

说明：
- 本脚本不绑定具体搜索引擎，Agent 执行通过 --agent-cmd 注入
- 可与不同 Agent 或搜索编排工具组合使用

示例（Dry Run，仅生成任务并评估）：
python scripts/run_auto_rounds.py ^
  --data cases/case01-nev-carbon/data/charging_piles_by_province.csv ^
  --value-col public_charging_piles ^
  --year-start 2017 ^
  --year-end 2023

示例（带 Agent 命令模板）：
python scripts/run_auto_rounds.py ^
  --data cases/case01-nev-carbon/data/charging_piles_by_province.csv ^
  --value-col public_charging_piles ^
  --year-start 2017 ^
  --year-end 2023 ^
  --agent-cmd "your_agent_runner --task {task_file}" ^
  --validate-cmd "python scripts/validate_round.py --data {data} --registry cases/case01-nev-carbon/data/source_registry.csv --variable charging --value-col public_charging_piles --check-unit 台"
"""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import os
import shlex
import subprocess
import sys
from collections import Counter
from collections.abc import Iterable

from tools.gap_analysis import compute_missing
from tools.io import load_csv
from tools.logging_utils import configure_logging
from tools.province_mapper import PROVINCE_MAP, normalize

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def parse_csv_list(raw: str) -> list[str]:
    return [x.strip() for x in (raw or "").split(",") if x.strip()]


def run_command(cmd: Iterable[str] | str, cwd: str) -> int:
    cmd_list = shlex.split(cmd) if isinstance(cmd, str) else list(cmd)
    logging.info("[CMD] %s", " ".join(shlex.quote(x) for x in cmd_list))
    result = subprocess.run(cmd_list, cwd=cwd)
    return result.returncode


def _norm_value_for_key(col: str, raw: str) -> str:
    v = (raw or "").strip()
    if col == "province" and v:
        try:
            return normalize(v, "short")
        except ValueError:
            return v
    if col == "year" and v and v.isdigit():
        return str(int(v))
    return v


def _row_key(row: dict, key_cols: list[str]) -> tuple:
    return tuple(_norm_value_for_key(c, row.get(c) or "") for c in key_cols)


def coverage_stats(
    rows: list[dict], key_cols: list[str], value_cols: list[str], years: list[int] | None = None
) -> dict:
    total = len(rows)
    filled_keys: set[tuple] = set()
    all_keys: set[tuple] = set()
    per_col_non_empty = Counter()
    per_year_filled = Counter()

    for r in rows:
        key = _row_key(r, key_cols)
        all_keys.add(key)
        has_value = False
        for c in value_cols:
            if (r.get(c) or "").strip():
                per_col_non_empty[c] += 1
                has_value = True
        if has_value:
            filled_keys.add(key)
            y = (r.get("year") or "").strip()
            if y.isdigit():
                per_year_filled[int(y)] += 1

    # 若key为 province+year 且给了年份范围，使用 30省×年份 的完整宇宙作为分母
    if years and set(key_cols) == {"province", "year"}:
        universe = set()
        for p in PROVINCE_MAP:
            for y in years:
                key_parts = []
                for col in key_cols:
                    if col == "province":
                        key_parts.append(p)
                    elif col == "year":
                        key_parts.append(str(y))
                universe.add(tuple(key_parts))
        all_keys = universe

    return {
        "total_rows": total,
        "all_keys_count": len(all_keys),
        "filled_keys": filled_keys,
        "filled_keys_count": len(filled_keys),
        "fill_rate": (len(filled_keys) / len(all_keys) * 100) if all_keys else 0.0,
        "per_col_non_empty": dict(per_col_non_empty),
        "per_year_filled": dict(sorted(per_year_filled.items())),
    }


def write_report(path: str, report_lines: list[str]):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")


def main():
    configure_logging()
    parser = argparse.ArgumentParser(description="多轮自动调度")
    parser.add_argument("--data", required=True, help="目标数据CSV")
    parser.add_argument("--value-col", required=True, help="目标数值列（逗号分隔）")
    parser.add_argument("--key", default="province,year", help="主键列（逗号分隔）")
    parser.add_argument("--year-start", type=int, required=True, help="起始年份")
    parser.add_argument("--year-end", type=int, required=True, help="结束年份")
    parser.add_argument("--top-years", type=int, default=2, help="每轮优先年份数")
    parser.add_argument("--keyword-name", default=None, help="关键词指标名")
    parser.add_argument("--keyword-template1", default="{省名} {keyword_name} {year} 保有量 台")
    parser.add_argument("--keyword-template2", default="{省名} {keyword_name} {year} 截至 台")
    parser.add_argument("--task-output", default=None, help="任务文件输出路径（默认: 与 --data 同目录）")
    parser.add_argument("--max-rounds", type=int, default=5, help="最大轮数")
    parser.add_argument("--min-gain", type=int, default=1, help="单轮最小新增键数")
    parser.add_argument("--patience", type=int, default=1, help="连续低增益容忍轮数")
    parser.add_argument(
        "--agent-cmd", default=None, help="Agent执行命令模板（支持 {task_file}/{round}/{data}/{repo_root}）"
    )
    parser.add_argument("--validate-cmd", default=None, help="校验命令模板（同上占位符）")
    parser.add_argument("--report", default=None, help="报告输出md（默认: 与 --data 同目录）")
    args = parser.parse_args()

    key_cols = parse_csv_list(args.key)
    value_cols = parse_csv_list(args.value_col)
    if not value_cols:
        raise ValueError("--value-col 不能为空")
    if args.year_start > args.year_end:
        raise ValueError("--year-start 不能大于 --year-end")

    data_dir = os.path.dirname(os.path.abspath(args.data))
    task_output = args.task_output or os.path.join(data_dir, "next-round-task.md")
    report_output = args.report or os.path.join(data_dir, "auto-round-report.md")

    years = list(range(args.year_start, args.year_end + 1))
    report_lines = []
    report_lines.append(f"# 自动多轮搜索报告（{dt.datetime.now().isoformat(timespec='seconds')}）")
    report_lines.append("")
    report_lines.append(f"- 数据文件：`{args.data}`")
    report_lines.append(f"- 主键：`{','.join(key_cols)}`")
    report_lines.append(f"- 数值列：`{','.join(value_cols)}`")
    report_lines.append(f"- 轮数上限：{args.max_rounds}")
    report_lines.append("")

    before_rows = load_csv(args.data)
    before_stats = coverage_stats(before_rows, key_cols, value_cols, years=years)
    missing_before = compute_missing(before_rows, years, value_cols[0])
    total_missing_before = sum(len(v) for v in missing_before.values())
    report_lines.append("## 初始状态")
    report_lines.append(
        f"- 已覆盖键数：{before_stats['filled_keys_count']} / {before_stats['all_keys_count']} ({before_stats['fill_rate']:.1f}%)"
    )
    report_lines.append(f"- 年份缺失总数（按 `{value_cols[0]}`）：{total_missing_before}")
    report_lines.append("")

    low_gain_streak = 0
    executed_rounds = 0

    for r in range(1, args.max_rounds + 1):
        current_rows = load_csv(args.data)
        current_missing = compute_missing(current_rows, years, value_cols[0])
        current_missing_total = sum(len(v) for v in current_missing.values())
        if current_missing_total == 0:
            report_lines.append(f"## Round {r}")
            report_lines.append("- 缺口已为0，提前停止。")
            report_lines.append("")
            break

        report_lines.append(f"## Round {r}")
        report_lines.append(f"- 本轮前缺失总数：{current_missing_total}")

        # 1) 生成任务
        run_round_cmd = [
            sys.executable,
            os.path.join(ROOT, "scripts", "run_round.py"),
            "--data",
            args.data,
            "--value-col",
            value_cols[0],
            "--year-start",
            str(args.year_start),
            "--year-end",
            str(args.year_end),
            "--top-years",
            str(args.top_years),
            "--keyword-name",
            args.keyword_name or value_cols[0],
            "--keyword-template1",
            args.keyword_template1,
            "--keyword-template2",
            args.keyword_template2,
            "--output",
            task_output,
        ]
        if run_command(run_round_cmd, cwd=ROOT) != 0:
            report_lines.append("- 任务生成失败，停止。")
            report_lines.append("")
            break
        report_lines.append(f"- 任务文件：`{task_output}`")

        # 2) 调用agent（可选）
        if args.agent_cmd:
            rendered = args.agent_cmd.format(
                task_file=task_output,
                round=r,
                data=args.data,
                repo_root=ROOT,
            )
            rc = run_command(rendered, cwd=ROOT)
            report_lines.append(f"- Agent命令退出码：{rc}")
            if rc != 0:
                report_lines.append("- Agent执行失败，停止。")
                report_lines.append("")
                break
        else:
            report_lines.append("- 未提供 --agent-cmd，本轮为 Dry Run（仅生成任务）。")
            report_lines.append("")
            executed_rounds = r
            break

        # 3) 校验（可选）
        if args.validate_cmd:
            rendered = args.validate_cmd.format(
                task_file=task_output,
                round=r,
                data=args.data,
                repo_root=ROOT,
            )
            rc = run_command(rendered, cwd=ROOT)
            report_lines.append(f"- 校验命令退出码：{rc}")
            if rc != 0:
                report_lines.append("- 校验失败，停止。")
                report_lines.append("")
                break

        # 4) 评估增益
        after_rows = load_csv(args.data)
        after_stats = coverage_stats(after_rows, key_cols, value_cols, years=years)
        gained = len(after_stats["filled_keys"] - before_stats["filled_keys"])
        after_missing = compute_missing(after_rows, years, value_cols[0])
        after_missing_total = sum(len(v) for v in after_missing.values())
        report_lines.append(f"- 本轮新增键数：{gained}")
        report_lines.append(f"- 本轮后缺失总数：{after_missing_total}")
        report_lines.append(f"- 覆盖率：{before_stats['fill_rate']:.1f}% -> {after_stats['fill_rate']:.1f}%")
        report_lines.append("")

        executed_rounds = r
        if gained < args.min_gain:
            low_gain_streak += 1
        else:
            low_gain_streak = 0

        before_stats = after_stats
        if low_gain_streak >= args.patience:
            report_lines.append(f"- 连续低增益达到 {low_gain_streak} 轮，提前停止。")
            report_lines.append("")
            break

    final_rows = load_csv(args.data)
    final_stats = coverage_stats(final_rows, key_cols, value_cols, years=years)
    report_lines.append("## 最终结果")
    report_lines.append(f"- 实际执行轮数：{executed_rounds}")
    report_lines.append(
        f"- 最终覆盖键数：{final_stats['filled_keys_count']} / {final_stats['all_keys_count']} ({final_stats['fill_rate']:.1f}%)"
    )
    report_lines.append(f"- 各数值列非空：{final_stats['per_col_non_empty']}")
    report_lines.append(f"- 各年份覆盖（按任一value-col有值）：{final_stats['per_year_filled']}")
    report_lines.append("")

    write_report(report_output, report_lines)
    logging.info("已输出报告: %s", report_output)


if __name__ == "__main__":
    main()
