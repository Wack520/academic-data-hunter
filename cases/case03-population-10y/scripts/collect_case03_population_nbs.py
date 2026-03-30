#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Case03 自动采集：30省年末常住人口（万人）
- 来源：国家统计局 国家数据（data.stats.gov.cn）
- 指标代码：A030101
- 年份：默认 2015-2024
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import tempfile
import textwrap
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

import requests
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
from province_mapper import get_all_provinces  # noqa: E402


BASE_URL = "https://data.stats.gov.cn"
CASE_DIR = ROOT / "cases" / "case03-population-10y"
DATA_DIR = CASE_DIR / "data"
PANEL_PATH = DATA_DIR / "population_by_province.csv"
REG_PATH = DATA_DIR / "source_registry.csv"
NBS_RAW_PATH = DATA_DIR / "nbs_resident_population_10k_person.csv"


@dataclass
class NBSMeta:
    code: str
    name: str
    unit: str
    source_url: str
    source_name: str = ""
    source_level: str = "A"
    note: str = ""


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="采集 case03 人口数据（NBS）")
    p.add_argument("--year-start", type=int, default=2015)
    p.add_argument("--year-end", type=int, default=2024)
    p.add_argument("--indicator-code", default="A030101")
    p.add_argument("--allow-local-fallback", action="store_true", default=True)
    return p.parse_args()


def _solve_challenge_js(js_text: str) -> Tuple[str, str]:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        js_file = td / "challenge.js"
        run_file = td / "run.js"
        js_file.write_text(js_text, encoding="utf-8")
        run_file.write_text(
            textwrap.dedent(
                f"""
                const fs=require('fs');
                const {{TextDecoder}}=require('util');
                global.TextDecoder=TextDecoder;
                let lastLocation='';
                const locationObj={{hostname:'data.stats.gov.cn',protocol:'https:',href:'https://data.stats.gov.cn/'}};
                const windowObj={{}};
                Object.defineProperty(windowObj,'location',{{
                  get(){{return locationObj;}},
                  set(v){{lastLocation=v; locationObj.href=v;}}
                }});
                global.window=windowObj;
                const doc={{
                  createElement:(tag)=>({{tagName:tag,style:{{}},appendChild:()=>{{}},submit:()=>{{}},setAttribute:()=>{{}}}}),
                  body:{{appendChild:()=>{{}}}},
                  cookie:''
                }};
                global.document=doc;
                global.setInterval=(fn,ms)=>0;
                global.clearInterval=(id)=>{{}};
                try {{
                  const code = fs.readFileSync({str(js_file)!r}, 'utf8');
                  eval(code);
                  console.log(JSON.stringify({{location:lastLocation,cookie:doc.cookie||''}}));
                }} catch(e) {{
                  console.log(JSON.stringify({{error:String(e&&e.stack?e.stack:e),location:lastLocation,cookie:doc.cookie||''}}));
                }}
                """
            ),
            encoding="utf-8",
        )
        proc = subprocess.run(["node", str(run_file)], capture_output=True, text=True, timeout=25)
        out = proc.stdout.strip().splitlines()
        if not out:
            raise RuntimeError(f"challenge js执行失败: {proc.stderr[:200]}")
        obj = json.loads(out[-1])
        if obj.get("error"):
            raise RuntimeError(f"challenge js错误: {obj['error'][:200]}")
        return obj.get("location", ""), obj.get("cookie", "")


def _apply_cookie_string(session: requests.Session, cookie_str: str) -> None:
    if not cookie_str:
        return
    for part in cookie_str.split(";"):
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        lk = k.strip().lower()
        if lk in {"path", "domain", "expires", "max-age", "secure", "httponly", "samesite"}:
            continue
        session.cookies.set(k.strip(), v.strip(), domain="data.stats.gov.cn")


def _request_with_challenge(session: requests.Session, url: str, max_rounds: int = 8) -> requests.Response:
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://data.stats.gov.cn/easyquery.htm?cn=E0103",
    }
    current = url
    for _ in range(max_rounds):
        resp = session.get(current, headers=headers, timeout=30)
        txt = resp.text.lstrip()
        if txt.startswith("{") or txt.startswith("["):
            return resp
        m = re.search(r"<script type=\"text/javascript\">(.*?)</script>", resp.text, re.S)
        if not m:
            raise RuntimeError(f"未找到challenge脚本: {resp.text[:120]}")
        nxt, cookie = _solve_challenge_js(m.group(1))
        _apply_cookie_string(session, cookie)
        if not nxt:
            raise RuntimeError("challenge返回空跳转")
        current = urllib.parse.urljoin(BASE_URL, nxt)
    raise RuntimeError("challenge轮次超限")


def fetch_population_nbs(session: requests.Session, code: str, year_start: int, year_end: int) -> Tuple[List[Dict], NBSMeta]:
    year_range = f"{year_start}-{year_end}"
    params = {
        "m": "QueryData",
        "dbcode": "fsnd",
        "rowcode": "reg",
        "colcode": "sj",
        "wds": json.dumps([{"wdcode": "zb", "valuecode": code}], ensure_ascii=False),
        "dfwds": json.dumps([{"wdcode": "sj", "valuecode": year_range}], ensure_ascii=False),
    }
    query_url = BASE_URL + "/easyquery.htm?" + urllib.parse.urlencode(params)
    resp = _request_with_challenge(session, query_url)
    payload = resp.json()
    rd = payload.get("returndata", {})

    wdnodes = rd.get("wdnodes", [])
    zb_nodes = next((x.get("nodes", []) for x in wdnodes if x.get("wdcode") == "zb"), [])
    reg_nodes = next((x.get("nodes", []) for x in wdnodes if x.get("wdcode") == "reg"), [])
    if not zb_nodes:
        raise RuntimeError(f"{code} 无zb节点")

    zb = zb_nodes[0]
    meta = NBSMeta(
        code=zb.get("code", code),
        name=zb.get("cname", zb.get("name", code)),
        unit=zb.get("unit", ""),
        source_url=query_url,
        source_name=f"国家统计局-国家数据({zb.get('cname', zb.get('name', code))})",
        source_level="A",
        note="NBS在线接口直采",
    )
    target_years = set(range(year_start, year_end + 1))
    target_provs = set(get_all_provinces("full"))
    reg_map = {x.get("code"): x.get("cname", x.get("name", "")) for x in reg_nodes}

    rows: List[Dict] = []
    for dn in rd.get("datanodes", []):
        wds = {w.get("wdcode"): w.get("valuecode") for w in dn.get("wds", [])}
        reg = wds.get("reg")
        sj = wds.get("sj")
        if reg not in reg_map:
            continue
        try:
            year = int(sj)
        except Exception:
            continue
        if year not in target_years:
            continue
        province = reg_map[reg]
        if province not in target_provs:
            continue
        data_obj = dn.get("data", {}) or {}
        val = data_obj.get("data") if data_obj.get("hasdata", False) else None
        rows.append(
            {
                "province": province,
                "year": year,
                "resident_population_10k_person": val,
            }
        )
    dedup: Dict[Tuple[str, int], Dict] = {}
    for r in rows:
        dedup[(r["province"], int(r["year"]))] = r
    out = sorted(dedup.values(), key=lambda x: (x["province"], int(x["year"])))
    return out, meta


def write_raw_nbs(rows: List[Dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with NBS_RAW_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["province", "year", "resident_population_10k_person"])
        w.writeheader()
        w.writerows(rows)


def load_local_fallback(year_start: int, year_end: int) -> Tuple[List[Dict], NBSMeta]:
    local = ROOT / "cases" / "case02-nev-emission-controls" / "data" / "nbs_resident_population_10k_person.csv"
    if not local.exists():
        raise FileNotFoundError(f"fallback file missing: {local}")
    rows = []
    with local.open("r", encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            try:
                y = int((r.get("year") or "").strip())
            except Exception:
                continue
            if y < year_start or y > year_end:
                continue
            rows.append(
                {
                    "province": (r.get("province") or "").strip(),
                    "year": y,
                    "resident_population_10k_person": r.get("resident_population_10k_person"),
                }
            )
    meta = NBSMeta(
        code="A030101",
        name="年末常住人口",
        unit="万人",
        source_url=local.resolve().as_uri(),
        source_name="本地缓存-NBS人口指标（来自case02）",
        source_level="A",
        note="当前环境NBS在线接口不可达，使用本地缓存回填",
    )
    return rows, meta


def update_panel(rows: List[Dict], meta: NBSMeta) -> Tuple[int, int]:
    panel = list(csv.DictReader(PANEL_PATH.open("r", encoding="utf-8-sig")))
    today = __import__("datetime").date.today().isoformat()
    m = {(r["province"], int(r["year"])): r for r in rows}
    filled = 0
    total = 0
    for r in panel:
        r.setdefault("source_level", "")
        r.setdefault("access_date", "")
        key = (r["province"], int(r["year"]))
        if key not in m:
            continue
        total += 1
        val = m[key].get("resident_population_10k_person")
        if val in ("", None):
            continue
        filled += 1
        r["resident_population_10k_person"] = str(val)
        r["source_id"] = "SRC_CASE03_NBS_POP_01"
        r["source_level"] = meta.source_level or "A"
        r["source_name"] = meta.source_name or f"国家统计局-国家数据({meta.name})"
        r["source_url"] = meta.source_url or "https://data.stats.gov.cn/easyquery.htm?cn=E0103"
        r["publish_date"] = ""
        r["access_date"] = today
        r["evidence"] = f"指标代码={meta.code}; 单位={meta.unit}; 年份={key[1]}"
        r["note"] = meta.note or "NBS API拉取，严格口径，不插值"

    with PANEL_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "province",
                "year",
                "resident_population_10k_person",
                "source_id",
                "source_level",
                "source_name",
                "source_url",
                "publish_date",
                "access_date",
                "evidence",
                "note",
            ],
        )
        w.writeheader()
        w.writerows(panel)
    return filled, total


def update_registry(meta: NBSMeta) -> None:
    rows = list(csv.DictReader(REG_PATH.open("r", encoding="utf-8-sig")))
    ids = {r.get("source_id", "") for r in rows}
    if "SRC_CASE03_NBS_POP_01" not in ids:
        rows.append(
            {
                "source_id": "SRC_CASE03_NBS_POP_01",
                "variable": "resident_population_10k_person",
                "source_level": meta.source_level or "A",
                "source_name": meta.source_name or f"国家统计局-国家数据({meta.name})",
                "source_url": meta.source_url or "https://data.stats.gov.cn/easyquery.htm?cn=E0103",
                "cross_check_url": "",
                "publish_date": "",
                "access_date": __import__("datetime").date.today().isoformat(),
                "evidence_file": "nbs_resident_population_10k_person.csv",
                "is_primary": "1",
                "note": (meta.note + "; " if meta.note else "") + f"指标代码={meta.code}; 单位={meta.unit}",
            }
        )

    with REG_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "source_id",
                "variable",
                "source_level",
                "source_name",
                "source_url",
                "cross_check_url",
                "publish_date",
                "access_date",
                "evidence_file",
                "is_primary",
                "note",
            ],
        )
        w.writeheader()
        w.writerows(rows)


def update_reports(year_start: int, year_end: int, filled: int) -> None:
    total = len(get_all_provinces("full")) * (year_end - year_start + 1)
    progress = CASE_DIR / "progress-report.md"
    progress.write_text(
        (
            "# 进度汇报（case03-population-10y）\n\n"
            f"更新时间：{__import__('datetime').date.today().isoformat()}\n\n"
            "## 当前进度\n\n"
            f"- 面板骨架：`{total}/{total}` 行\n"
            f"- 已填充：`{filled}/{total}`\n"
            f"- 覆盖率：`{(filled/total*100 if total else 0):.1f}%`\n\n"
            "## 下一步\n\n"
            "- 若存在缺口，按 next-round-task.md 逐轮补缺。\n"
        ),
        encoding="utf-8",
    )

    log = CASE_DIR / "search-log.md"
    log.write_text(
        (
            "# 搜索日志（case03-population-10y）\n\n"
            f"更新时间：{__import__('datetime').date.today().isoformat()}\n\n"
            "## Round 1（NBS 批量采集）\n\n"
            f"- 来源：国家统计局 国家数据（指标 A030101，{year_start}-{year_end}）\n"
            "- 结果：已写入 `population_by_province.csv` 与 `source_registry.csv`\n"
            "- 规则：严格模式，不插值、不估算\n"
        ),
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    if not PANEL_PATH.exists():
        raise FileNotFoundError(f"缺少数据文件: {PANEL_PATH}")
    if not REG_PATH.exists():
        raise FileNotFoundError(f"缺少来源台账: {REG_PATH}")

    session = requests.Session()
    try:
        rows, meta = fetch_population_nbs(session, args.indicator_code, args.year_start, args.year_end)
    except Exception as e:
        if not args.allow_local_fallback:
            raise
        print(f"[WARN] online NBS fetch failed: {e}")
        rows, meta = load_local_fallback(args.year_start, args.year_end)
        print("[WARN] switched to local fallback source")
    write_raw_nbs(rows)
    filled, total = update_panel(rows, meta)
    update_registry(meta)
    update_reports(args.year_start, args.year_end, filled)

    print(f"[OK] NBS raw: {NBS_RAW_PATH} rows={len(rows)}")
    print(f"[OK] panel updated: {filled}/{total}")
    print(f"[OK] registry updated: {REG_PATH}")


if __name__ == "__main__":
    main()
