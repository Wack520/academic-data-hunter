#!/usr/bin/env python3
"""
Case02 strict NEV 自动续跑入口（一条命令，无需对话继续）：
1) 先刷新 strict 面板（collect_case02_nev_strict_partial.py）
2) 对当下缺失省份执行多轮 Camoufox 搜索
3) 自动产出每轮 JSON + 汇总报告 + 状态快照
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CASE_DIR = ROOT / "cases" / "case02-nev-emission-controls"
DATA_DIR = CASE_DIR / "data"
PANEL_PATH = DATA_DIR / "panel_case02_strict_30prov_2012_2023.csv"
TMP_DIR = CASE_DIR / "tmp" / "autopilot"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Case02 strict NEV 自动续跑")
    p.add_argument("--year", type=int, default=2023)
    p.add_argument("--provinces", default="", help="可选：手工指定省份，逗号分隔；为空则按strict缺失自动读取")
    p.add_argument("--rounds", type=int, default=3, help="最多自动轮数")
    p.add_argument("--run-mode", choices=["headless", "headed", "virtual"], default="headless")
    p.add_argument("--discover-config", default="", help="discover脚本配置文件（JSON/TOML）")
    p.add_argument("--engines", default="google,tavily,bing,sogou,360")
    p.add_argument("--domain-filter", default="gov.cn")
    p.add_argument("--google-max-results", type=int, default=15)
    p.add_argument("--google-hl", default="zh-CN")
    p.add_argument("--google-gl", default="")
    p.add_argument("--tavily-api-key", default="")
    p.add_argument("--tavily-endpoint", default="https://api.tavily.com/search")
    p.add_argument("--tavily-max-results", type=int, default=10)
    p.add_argument("--tavily-topic", default="general")
    p.add_argument("--max-pages", type=int, default=30)
    p.add_argument("--max-fetch-pages", type=int, default=20)
    p.add_argument("--fetch-workers", type=int, default=8)
    p.add_argument("--province-workers", type=int, default=1, help="省份并发worker数（每个worker独立浏览器）")
    p.add_argument(
        "--engine-mode",
        choices=["first", "merge"],
        default="merge",
        help="搜索引擎模式：first=首个命中；merge=合并多引擎结果（默认）",
    )
    p.add_argument("--per-domain-cap", type=int, default=3, help="每省同域名保留URL上限（0为不限制）")
    p.add_argument("--delay-min-ms", type=int, default=800)
    p.add_argument("--delay-max-ms", type=int, default=1800)
    p.add_argument("--query-timeout-ms", type=int, default=45000)
    p.add_argument("--request-timeout-sec", type=int, default=18)
    p.add_argument("--sleep-sec", type=int, default=2, help="轮次间隔秒数")
    p.add_argument("--output-dir", default=str(TMP_DIR))
    p.add_argument("--skip-processing", action="store_true", help="跳过 discover 后的数据处理层")
    p.add_argument("--process-mode", choices=["markdown", "extract", "both"], default="both")
    p.add_argument(
        "--process-schema-file",
        default="templates/extraction-schema-template.json",
        help="处理层 schema 文件",
    )
    p.add_argument("--process-max-urls", type=int, default=80, help="处理层最大URL数")
    p.add_argument("--process-timeout-sec", type=int, default=18, help="处理层请求超时秒数")
    p.add_argument("--process-retry", type=int, default=1, help="处理层重试次数")
    p.add_argument("--force", action="store_true", help="discover 不使用 resume")
    p.add_argument("--fresh-output", action="store_true", help="清理 autopilot 旧产物后再跑")
    p.add_argument("--skip-collect", action="store_true", help="跳过 collect 刷新（提速）")
    return p.parse_args()


def run_cmd(cmd: list[str], cwd: Path) -> int:
    print("[CMD]", " ".join(cmd))
    return subprocess.run(cmd, cwd=str(cwd)).returncode


def load_missing_provinces(year: int) -> list[str]:
    rows = list(csv.DictReader(PANEL_PATH.open("r", encoding="utf-8-sig")))
    rows = [r for r in rows if (r.get("year") or "").strip() == str(year)]
    return sorted([r["province"] for r in rows if not (r.get("nev_stock_10k") or "").strip()])


def sum_candidates(path: Path, provinces: list[str]) -> tuple[int, int]:
    if not path.exists():
        return 0, 0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return 0, 0
    total_cands = 0
    total_urls = 0
    for p in provinces:
        rec = data.get(p, {}) if isinstance(data, dict) else {}
        total_cands += int(rec.get("candidate_count", 0) or 0)
        total_urls += int(rec.get("url_count", 0) or 0)
    return total_urls, total_cands


def main() -> None:
    args = parse_args()
    args.fetch_workers = max(1, int(args.fetch_workers))
    args.province_workers = max(1, int(args.province_workers))
    args.per_domain_cap = max(0, int(args.per_domain_cap))
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.fresh_output:
        for p in out_dir.glob("camoufox_round*.json"):
            p.unlink(missing_ok=True)
        for p in out_dir.glob("processed_round*"):
            if p.is_dir():
                for c in p.glob("*"):
                    if c.is_file():
                        c.unlink(missing_ok=True)
                with contextlib.suppress(Exception):
                    p.rmdir()
        (out_dir / "autopilot_report.md").unlink(missing_ok=True)

    report_path = out_dir / "autopilot_report.md"
    lines: list[str] = []
    lines.append("# Case02 strict NEV 自动续跑报告")
    lines.append(f"- 开始时间：{datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"- year={args.year}, rounds={args.rounds}, run_mode={args.run_mode}")
    lines.append(
        f"- engine_mode={args.engine_mode}, province_workers={args.province_workers}, "
        f"fetch_workers={args.fetch_workers}, per_domain_cap={args.per_domain_cap}"
    )
    lines.append("")

    # Step 1: 先刷新 strict 面板（把现有 SOURCES 写入面板）
    rc = 0
    if not args.skip_collect:
        rc = run_cmd(
            [sys.executable, "cases/case02-nev-emission-controls/scripts/collect_case02_nev_strict_partial.py"], ROOT
        )
    lines.append("## 面板刷新")
    if args.skip_collect:
        lines.append("- collect_case02_nev_strict_partial.py skipped")
    else:
        lines.append(f"- collect_case02_nev_strict_partial.py rc={rc}")
    lines.append("")
    if rc != 0:
        report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        raise SystemExit(rc)

    prev_total_cands = None
    last_out = None
    for r in range(1, max(1, args.rounds) + 1):
        if args.provinces.strip():
            missing = [x.strip() for x in args.provinces.split(",") if x.strip()]
        else:
            missing = load_missing_provinces(args.year)
        lines.append(f"## Round {r}")
        lines.append(f"- missing({len(missing)}): {'、'.join(missing) if missing else '-'}")
        if not missing:
            lines.append("- 缺口为0，提前结束")
            lines.append("")
            break

        out_json = out_dir / f"camoufox_round{r}_missing{len(missing)}.json"
        provinces_arg = ",".join(missing)
        cmd = [
            sys.executable,
            "cases/case02-nev-emission-controls/scripts/discover_case02_nev_camoufox.py",
            "--year",
            str(args.year),
            "--provinces",
            provinces_arg,
            "--run-mode",
            args.run_mode,
            "--engines",
            args.engines,
            "--domain-filter",
            args.domain_filter,
            "--google-max-results",
            str(args.google_max_results),
            "--google-hl",
            str(args.google_hl),
            "--max-pages",
            str(args.max_pages),
            "--max-fetch-pages",
            str(args.max_fetch_pages),
            "--fetch-workers",
            str(args.fetch_workers),
            "--province-workers",
            str(args.province_workers),
            "--engine-mode",
            str(args.engine_mode),
            "--per-domain-cap",
            str(args.per_domain_cap),
            "--delay-min-ms",
            str(args.delay_min_ms),
            "--delay-max-ms",
            str(args.delay_max_ms),
            "--query-timeout-ms",
            str(args.query_timeout_ms),
            "--request-timeout-sec",
            str(args.request_timeout_sec),
            "--output",
            str(out_json),
        ]
        if args.google_gl:
            cmd.extend(["--google-gl", str(args.google_gl)])
        if args.tavily_api_key:
            cmd.extend(["--tavily-api-key", str(args.tavily_api_key)])
        if args.tavily_endpoint:
            cmd.extend(["--tavily-endpoint", str(args.tavily_endpoint)])
        if args.tavily_max_results:
            cmd.extend(["--tavily-max-results", str(args.tavily_max_results)])
        if args.tavily_topic:
            cmd.extend(["--tavily-topic", str(args.tavily_topic)])
        if args.discover_config:
            cmd.extend(["--config", str(args.discover_config)])
        if not args.force:
            cmd.append("--resume")
        rc = run_cmd(cmd, ROOT)
        lines.append(f"- discover rc={rc}")
        urls, cands = sum_candidates(out_json, missing)
        lines.append(f"- urls={urls}, candidates={cands}, out=`{out_json.as_posix()}`")
        process_out = out_dir / f"processed_round{r}"
        process_rc = 0
        if not args.skip_processing:
            process_cmd = [
                sys.executable,
                "scripts/process_web_data_pipeline.py",
                "--input-json",
                str(out_json),
                "--schema-file",
                str(args.process_schema_file),
                "--output-dir",
                str(process_out),
                "--mode",
                str(args.process_mode),
                "--max-urls",
                str(args.process_max_urls),
                "--timeout-sec",
                str(args.process_timeout_sec),
                "--retry",
                str(args.process_retry),
            ]
            process_rc = run_cmd(process_cmd, ROOT)
            lines.append(f"- process rc={process_rc}, out=`{process_out.as_posix()}`")
        else:
            lines.append("- process skipped")
        lines.append("")
        last_out = out_json

        if rc != 0:
            break
        if (not args.skip_processing) and process_rc != 0:
            lines.append("- 处理层失败，提前停止。")
            lines.append("")
            break
        if prev_total_cands is not None and cands <= prev_total_cands:
            lines.append(f"- 候选未提升（{prev_total_cands} -> {cands}），提前停止。")
            lines.append("")
            break
        prev_total_cands = cands
        if r < args.rounds and args.sleep_sec > 0:
            time.sleep(args.sleep_sec)

    if last_out:
        status_cmd = [
            sys.executable,
            "cases/case02-nev-emission-controls/scripts/report_case02_nev_strict_status.py",
            "--year",
            str(args.year),
            "--candidates",
            str(last_out),
            "--output",
            "cases/case02-nev-emission-controls/strict-nev-status.md",
        ]
        if args.provinces.strip():
            status_cmd.extend(["--provinces", args.provinces])
        run_cmd(
            status_cmd,
            ROOT,
        )
        lines.append("## 最终状态快照")
        lines.append(f"- candidates=`{last_out.as_posix()}`")
        lines.append("- status=`cases/case02-nev-emission-controls/strict-nev-status.md`")
        lines.append("")

    lines.append(f"- 结束时间：{datetime.now().isoformat(timespec='seconds')}")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[DONE] report: {report_path}")


if __name__ == "__main__":
    main()
