#!/usr/bin/env python3
"""
从 discover_case03_population_2024.py 的候选结果中，生成 2024 年常住人口严格复核清单。

说明：
- 本脚本只做“候选收敛 + 证据整理”，不直接改面板；
- 输出结果供人工二审后，再回填主面板。
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[3]
CASE_DIR = ROOT / "cases" / "case03-population-10y"
DEFAULT_IN = CASE_DIR / "tmp" / "population_2024_candidates.json"
DEFAULT_OUT = CASE_DIR / "data" / "population_2024_shortlist_review.csv"
DEFAULT_MD = CASE_DIR / "tmp" / "population_2024_shortlist_report.md"

PROVINCES = [
    "北京市",
    "天津市",
    "河北省",
    "山西省",
    "内蒙古自治区",
    "辽宁省",
    "吉林省",
    "黑龙江省",
    "上海市",
    "江苏省",
    "浙江省",
    "安徽省",
    "福建省",
    "江西省",
    "山东省",
    "河南省",
    "湖北省",
    "湖南省",
    "广东省",
    "广西壮族自治区",
    "海南省",
    "重庆市",
    "四川省",
    "贵州省",
    "云南省",
    "陕西省",
    "甘肃省",
    "青海省",
    "宁夏回族自治区",
    "新疆维吾尔自治区",
]

PROV_SHORT = {
    "北京市": "北京",
    "天津市": "天津",
    "河北省": "河北",
    "山西省": "山西",
    "内蒙古自治区": "内蒙古",
    "辽宁省": "辽宁",
    "吉林省": "吉林",
    "黑龙江省": "黑龙江",
    "上海市": "上海",
    "江苏省": "江苏",
    "浙江省": "浙江",
    "安徽省": "安徽",
    "福建省": "福建",
    "江西省": "江西",
    "山东省": "山东",
    "河南省": "河南",
    "湖北省": "湖北",
    "湖南省": "湖南",
    "广东省": "广东",
    "广西壮族自治区": "广西",
    "海南省": "海南",
    "重庆市": "重庆",
    "四川省": "四川",
    "贵州省": "贵州",
    "云南省": "云南",
    "陕西省": "陕西",
    "甘肃省": "甘肃",
    "青海省": "青海",
    "宁夏回族自治区": "宁夏",
    "新疆维吾尔自治区": "新疆",
}

OTHER_PROV_HINTS = [PROV_SHORT[p] for p in PROVINCES]

YEAR_PAT = re.compile(r"(?:2024年|截至2024年末|2024年末)")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="生成 case03 2024 人口严格复核清单")
    p.add_argument("--input", default=str(DEFAULT_IN), help="discover 输出 JSON")
    p.add_argument("--output", default=str(DEFAULT_OUT), help="复核清单 CSV")
    p.add_argument("--report", default=str(DEFAULT_MD), help="汇总报告 MD")
    p.add_argument("--min-confidence", type=int, default=28, help="最低置信分（默认 28）")
    return p.parse_args()


def host_score(url: str) -> int:
    host = (urlparse(url).hostname or "").lower()
    score = 0
    if host.endswith(".gov.cn"):
        score += 4
    if "tjj." in host:
        score += 6
    if "stats." in host:
        score += 4
    return score


def source_level_suggest(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    path = (urlparse(url).path or "").lower()
    if "tjj." in host or "stats." in host or "tjgb" in path:
        return "A-候选"
    if host.endswith(".gov.cn"):
        return "B-候选"
    return "C-候选"


def has_other_province(sentence: str, cur: str) -> bool:
    cur_short = PROV_SHORT[cur]
    for kw in OTHER_PROV_HINTS:
        if kw == cur_short:
            continue
        if kw and kw in sentence:
            return True
    return False


def score_candidate(province: str, c: dict) -> tuple[int, list[str]]:
    sentence = (c.get("sentence") or "").strip()
    url = (c.get("url") or "").strip()
    value = c.get("value_10k_person")
    base = int(c.get("score", 0)) + int(c.get("search_score", 0))
    reason: list[str] = []

    if value is None:
        return -10_000, ["value_missing"]
    try:
        float(value)
    except Exception:
        return -10_000, ["value_non_numeric"]

    if not YEAR_PAT.search(sentence):
        return -10_000, ["year_2024_not_explicit"]
    reason.append("year=2024")

    short = PROV_SHORT[province]
    has_explicit = bool(c.get("explicit_province_in_sentence")) or (short in sentence or province in sentence)
    has_scope = any(x in sentence for x in ["全省", "全市", "全区", "我省", "我市", "我区"])
    if not (has_explicit or has_scope):
        return -10_000, ["province_scope_not_clear"]
    if has_scope:
        reason.append("scope")
        base += 4
    if has_explicit:
        reason.append("explicit_province")
        base += 4

    if has_other_province(sentence, province):
        return -10_000, ["contains_other_province"]

    if "常住人口" not in sentence:
        return -10_000, ["keyword_missing"]

    h = host_score(url)
    base += h
    reason.append(f"host+{h}")

    if "统计公报" in sentence or "国民经济和社会发展" in sentence:
        base += 3
        reason.append("bulletin_like")

    return base, reason


def main() -> None:
    args = parse_args()
    in_path = Path(args.input)
    out_path = Path(args.output)
    rep_path = Path(args.report)

    if not in_path.exists():
        raise FileNotFoundError(f"input not found: {in_path}")
    data = json.loads(in_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("input json must be object")

    rows: list[dict] = []
    missing: list[str] = []
    rejected: dict[str, int] = {}

    for prov in PROVINCES:
        rec = data.get(prov) or {}
        cands = rec.get("top_candidates") or []
        best = None
        best_score = -10_000
        best_reason = []
        rej = 0
        for c in cands:
            sc, reason = score_candidate(prov, c)
            if sc <= -10_000:
                rej += 1
                continue
            if sc > best_score:
                best = c
                best_score = sc
                best_reason = reason
        rejected[prov] = rej
        if best is None or best_score < int(args.min_confidence):
            missing.append(prov)
            continue

        val = float(best["value_10k_person"])
        rows.append(
            {
                "province": prov,
                "year": "2024",
                "resident_population_10k_person": f"{val:.6f}".rstrip("0").rstrip("."),
                "source_level_suggest": source_level_suggest(best.get("url", "")),
                "source_url": best.get("url", ""),
                "search_engine": best.get("search_engine", ""),
                "search_query": best.get("search_query", ""),
                "confidence": str(best_score),
                "evidence_sentence": (best.get("sentence") or "")[:500],
                "rule_flags": ";".join(best_reason),
            }
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "province",
                "year",
                "resident_population_10k_person",
                "source_level_suggest",
                "source_url",
                "search_engine",
                "search_query",
                "confidence",
                "evidence_sentence",
                "rule_flags",
            ],
        )
        w.writeheader()
        w.writerows(rows)

    rep_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Case03 2024 常住人口短名单报告",
        "",
        f"- 输入文件：`{in_path}`",
        f"- 输出清单：`{out_path}`",
        f"- 通过省份：**{len(rows)} / 30**",
        f"- 未通过省份：**{len(missing)} / 30**",
        f"- 最低置信分阈值：`{args.min_confidence}`",
        "",
        "## 未通过省份",
        ", ".join(missing) if missing else "无",
        "",
        "## 通过项（省份 / 值 / 置信分）",
    ]
    for r in rows:
        lines.append(
            f"- {r['province']} / {r['resident_population_10k_person']} 万人 / conf={r['confidence']} / {r['source_url']}"
        )
    rep_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"[OK] shortlist rows={len(rows)} => {out_path}")
    print(f"[OK] missing={len(missing)} => {', '.join(missing)}")
    print(f"[OK] report => {rep_path}")


if __name__ == "__main__":
    main()
