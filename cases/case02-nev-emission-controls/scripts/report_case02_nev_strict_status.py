#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Case02 严格口径（NEV）状态汇总：
- strict 面板覆盖率
- 缺失省份列表
- 候选发现结果摘要（可选）
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CASE_DIR = ROOT / "cases" / "case02-nev-emission-controls"
PANEL_PATH = CASE_DIR / "data" / "panel_case02_strict_30prov_2012_2023.csv"
DEFAULT_CANDIDATES = CASE_DIR / "tmp" / "camoufox_missing7_v2.json"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="汇总 Case02 strict NEV 覆盖与候选状态")
    p.add_argument("--year", type=int, default=2023)
    p.add_argument("--panel", default=str(PANEL_PATH))
    p.add_argument("--candidates", default=str(DEFAULT_CANDIDATES))
    p.add_argument("--provinces", default="", help="可选：仅展示这些省份（逗号分隔）")
    p.add_argument("--top", type=int, default=2, help="每省展示前N条候选")
    p.add_argument("--output", default="", help="可选，输出 markdown 文件路径")
    return p.parse_args()


def load_panel(path: Path, year: int):
    rows = list(csv.DictReader(path.open("r", encoding="utf-8-sig")))
    rows = [r for r in rows if (r.get("year") or "").strip() == str(year)]
    rows = sorted(rows, key=lambda x: x["province"])
    filled = [r for r in rows if (r.get("nev_stock_10k") or "").strip()]
    missing = [r["province"] for r in rows if not (r.get("nev_stock_10k") or "").strip()]
    return rows, filled, missing


def render_report(
    year: int,
    rows: list[dict],
    filled: list[dict],
    missing: list[str],
    cand_path: Path,
    top: int,
    provinces_filter: list[str] | None = None,
) -> str:
    lines: list[str] = []
    lines.append(f"# Case02 strict NEV 状态（{year}）")
    lines.append("")
    lines.append(f"- 面板路径：`{PANEL_PATH.as_posix()}`")
    lines.append(f"- 覆盖：**{len(filled)}/{len(rows)}**")
    lines.append(f"- 缺失省份（{len(missing)}）：{'、'.join(missing) if missing else '-'}")
    lines.append("")

    missing_to_show = missing
    if provinces_filter:
        pf = [x.strip() for x in provinces_filter if x.strip()]
        missing_to_show = [p for p in missing if p in pf]
        lines.append(f"- 展示范围：{'、'.join(missing_to_show) if missing_to_show else '（无）'}")
        lines.append("")

    if not cand_path.exists():
        lines.append(f"> 候选文件不存在：`{cand_path.as_posix()}`")
        return "\n".join(lines)

    try:
        data = json.loads(cand_path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        lines.append(f"> 候选文件读取失败：{e}")
        return "\n".join(lines)

    lines.append(f"## 候选摘要（`{cand_path.name}`）")
    lines.append("")
    for prov in missing_to_show:
        rec = data.get(prov, {}) if isinstance(data, dict) else {}
        cnt = int(rec.get("candidate_count", 0) or 0)
        url_cnt = int(rec.get("url_count", 0) or 0)
        anti = int(rec.get("anti_spider_hits", 0) or 0)
        lines.append(f"### {prov}")
        lines.append(f"- urls={url_cnt}, candidates={cnt}, anti_hits={anti}")
        tops = rec.get("top_candidates", []) if isinstance(rec, dict) else []
        if not tops:
            lines.append("- top: （无）")
            lines.append("")
            continue
        for i, c in enumerate(tops[: max(1, top)], 1):
            sent = (c.get("sentence") or "").replace("\n", " ").strip()
            sent = re.sub(r"[\ue000-\uf8ff]", "", sent)
            if len(sent) > 96:
                sent = sent[:96] + "..."
            lines.append(
                f"- {i}) score={c.get('score')} value_10k={c.get('value_10k')} "
                f"url={c.get('url')} | {sent}"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    args = parse_args()
    panel = Path(args.panel)
    cand = Path(args.candidates)
    rows, filled, missing = load_panel(panel, args.year)
    provinces_filter = [x.strip() for x in (args.provinces or "").split(",") if x.strip()]
    report = render_report(args.year, rows, filled, missing, cand, args.top, provinces_filter=provinces_filter)
    print(report)
    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        print(f"[OK] report saved: {out}")


if __name__ == "__main__":
    main()
