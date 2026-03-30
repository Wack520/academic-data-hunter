#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Case03 严格补采（Round3）：补齐 2024 年剩余省份常住人口。

目标：
- 在 `population_by_province_strict_partial.csv` 基础上，补齐 2024 缺口；
- 仅采信可复核的官方/权威页面原文，不做插值外推。
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List

import requests
import urllib3
from bs4 import BeautifulSoup
from camoufox.sync_api import Camoufox

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


ROOT = Path(__file__).resolve().parents[3]
CASE_DIR = ROOT / "cases" / "case03-population-10y"
DATA_DIR = CASE_DIR / "data"

PANEL_PATH = DATA_DIR / "population_by_province_strict_partial.csv"
REG_PATH = DATA_DIR / "source_registry_strict_partial.csv"
EVIDENCE_PATH = DATA_DIR / "population_2024_round3_evidence.csv"


@dataclass
class SourceSpec:
    province: str
    source_id: str
    source_level: str
    source_name: str
    source_url: str
    regex: str
    note: str
    use_camoufox: bool = False


SPECS: List[SourceSpec] = [
    SourceSpec(
        province="天津市",
        source_id="SRC_CASE03_POP2024_R3_TJ",
        source_level="A",
        source_name="天津市人民政府-2024年天津市国民经济和社会发展统计公报",
        source_url="https://www.tj.gov.cn/sq/tjgb/202503/t20250324_6890361.html",
        regex=r"年末全市常住人口总量\s*([0-9]+(?:\.[0-9]+)?)\s*万人",
        note="2024统计公报正文口径。",
    ),
    SourceSpec(
        province="山西省",
        source_id="SRC_CASE03_POP2024_R3_SX",
        source_level="A",
        source_name="山西省统计局-2024年山西省国民经济和社会发展统计公报",
        source_url="http://tjj.shanxi.gov.cn/tjsj/tjgb/ndtjgb/202503/t20250327_9797517.shtml",
        regex=r"年末全省常住人口\s*([0-9]+(?:\.[0-9]+)?)\s*万人",
        note="2024统计公报正文口径。",
    ),
    SourceSpec(
        province="内蒙古自治区",
        source_id="SRC_CASE03_POP2024_R3_NM",
        source_level="A",
        source_name="内蒙古自治区人民政府-人口（2024年人口主要数据）",
        source_url="https://www.nmg.gov.cn/asnmg/shjj/rk/index_2383.html",
        regex=r"2024年末[^。]{0,40}?全区常住人口\s*([0-9]+(?:\.[0-9]+)?)\s*万人",
        note="自治区政府省情页，人口抽样调查推算数据。",
    ),
    SourceSpec(
        province="辽宁省",
        source_id="SRC_CASE03_POP2024_R3_LN",
        source_level="A",
        source_name="辽宁省人民政府-人口与民族（来源省统计局）",
        source_url="https://www.ln.gov.cn/web/sqgk/rkymz/2025101310563144642/index.shtml",
        regex=r"2024年末常住人口\s*([0-9]+(?:\.[0-9]+)?)\s*万人",
        note="省政府发布页面注明来源为省统计局网站。",
    ),
    SourceSpec(
        province="吉林省",
        source_id="SRC_CASE03_POP2024_R3_JL",
        source_level="A",
        source_name="吉林省统计局-2024年吉林省国民经济和社会发展统计公报",
        source_url="https://tjj.jl.gov.cn/tjsj/tjgb/ndgb/202503/t20250324_3419691.html",
        regex=r"年末全省总人口为\s*([0-9]+(?:\.[0-9]+)?)\s*万人[^。]{0,80}其中城镇常住人口",
        note="公报以“全省总人口”表述，后接城镇常住人口结构信息。",
    ),
    SourceSpec(
        province="黑龙江省",
        source_id="SRC_CASE03_POP2024_R3_HLJ",
        source_level="A",
        source_name="黑龙江省人民政府-2024年黑龙江省国民经济和社会发展统计公报",
        source_url="https://www.hlj.gov.cn/hlj/c108419/202504/c00_31866784.shtml",
        regex=r"年末常住总人口\s*([0-9]+(?:\.[0-9]+)?)\s*万人",
        note="2024统计公报正文口径。",
    ),
    SourceSpec(
        province="上海市",
        source_id="SRC_CASE03_POP2024_R3_SH",
        source_level="A",
        source_name="上海市统计局-2024年上海市国民经济和社会发展统计公报",
        source_url="https://tjj.sh.gov.cn/tjgb/20250324/a7fe18c6d5c24d66bfca89c5bb4cdcfb.html",
        regex=r"全市常住人口为\s*([0-9]+(?:\.[0-9]+)?)\s*万人",
        note="2024统计公报正文口径。",
    ),
    SourceSpec(
        province="江苏省",
        source_id="SRC_CASE03_POP2024_R3_JS",
        source_level="A",
        source_name="江苏省人民政府-人口区划（2024年末常住人口）",
        source_url="https://www.jiangsu.gov.cn/col/col88749/index.html",
        regex=r"2024年末[^。]{0,30}?全省常住人口\s*([0-9]+(?:\.[0-9]+)?)\s*万人",
        note="江苏政府省情页人口条目，含2024年末常住人口。",
        use_camoufox=True,
    ),
    SourceSpec(
        province="福建省",
        source_id="SRC_CASE03_POP2024_R3_FJ",
        source_level="A",
        source_name="福建省人民政府-2024年福建省国民经济和社会发展统计公报",
        source_url="https://www.fujian.gov.cn/zwgk/sjfb/tjgb/202503/t20250313_6779048.htm",
        regex=r"年末常住人口\s*([0-9]+(?:\.[0-9]+)?)\s*万人",
        note="2024统计公报正文口径。",
    ),
    SourceSpec(
        province="山东省",
        source_id="SRC_CASE03_POP2024_R3_SD",
        source_level="A",
        source_name="山东省统计局-2024年山东省国民经济和社会发展统计公报",
        source_url="http://tjj.shandong.gov.cn/art/2025/3/5/art_104039_10316728.html",
        regex=r"年末常住人口\s*([0-9]+(?:\.[0-9]+)?)\s*万人",
        note="2024统计公报正文口径。",
    ),
    SourceSpec(
        province="湖北省",
        source_id="SRC_CASE03_POP2024_R3_HB",
        source_level="A",
        source_name="湖北省统计局-2024年湖北省国民经济和社会发展统计公报",
        source_url="https://tjj.hubei.gov.cn/tjsj/tjgb/ndtjgb/qstjgb/202503/t20250321_5585085.shtml",
        regex=r"年末全省常住人口\s*([0-9]+(?:\.[0-9]+)?)\s*万人",
        note="2024统计公报正文口径。",
    ),
    SourceSpec(
        province="湖南省",
        source_id="SRC_CASE03_POP2024_R3_HN",
        source_level="A",
        source_name="湖南省人民政府-2024年湖南省国民经济和社会发展统计公报",
        source_url="http://www.hunan.gov.cn/hnszf/zfsj/tjgb/202503/t20250321_33620617.html",
        regex=r"年末全省常住人口\s*([0-9]+(?:\.[0-9]+)?)\s*万人",
        note="2024统计公报正文口径。",
    ),
    SourceSpec(
        province="广西壮族自治区",
        source_id="SRC_CASE03_POP2024_R3_GX",
        source_level="A",
        source_name="广西壮族自治区统计局-2024年广西壮族自治区国民经济和社会发展统计公报",
        source_url="http://tjj.gxzf.gov.cn/tjsj/tjgb/qqgb/t19769919.shtml",
        regex=r"年末全区常住人口\s*\[[0-9]+\]\s*([0-9]+(?:\.[0-9]+)?)\s*万人",
        note="2024统计公报正文口径。",
    ),
    SourceSpec(
        province="重庆市",
        source_id="SRC_CASE03_POP2024_R3_CQ",
        source_level="A",
        source_name="重庆市统计局-2024年重庆市国民经济和社会发展统计公报",
        source_url="https://tjj.cq.gov.cn/zwgk_233/fdzdgknr/tjxx/sjzl_55471/tjgb_55472/202503/t20250326_14443791_wap.html",
        regex=r"年末全市常住人口\s*([0-9]+(?:\.[0-9]+)?)\s*万人",
        note="2024统计公报正文口径。",
    ),
    SourceSpec(
        province="云南省",
        source_id="SRC_CASE03_POP2024_R3_YN",
        source_level="B",
        source_name="云南人大网-转载《云南省2024年国民经济和社会发展统计公报》",
        source_url="https://www.ynrd.gov.cn/html/2025/yaowenzixun_0408/4032748.html",
        regex=r"年末全省常住人口\s*([0-9]+(?:\.[0-9]+)?)\s*万人",
        note="省级人大站转载统计公报文本（非统计局原站）。",
    ),
    SourceSpec(
        province="甘肃省",
        source_id="SRC_CASE03_POP2024_R3_GS",
        source_level="A",
        source_name="甘肃省人民政府-2024年甘肃省国民经济和社会发展统计公报",
        source_url="https://www.gansu.gov.cn/gsszf/gsyw/202503/174095898.shtml",
        regex=r"年末全省常住人口\s*([0-9]+(?:\.[0-9]+)?)\s*万人",
        note="目标页对 requests 返回 412，采用浏览器渲染提取正文。",
        use_camoufox=True,
    ),
    SourceSpec(
        province="宁夏回族自治区",
        source_id="SRC_CASE03_POP2024_R3_NX",
        source_level="B",
        source_name="宁夏日报电子版-转载《宁夏回族自治区2024年国民经济和社会发展统计公报》",
        source_url="https://szb.nxrb.cn/nxrb/pad/con/202504/25/content_157253.html",
        regex=r"年末全区常住人口\s*([0-9]+(?:\.[0-9]+)?)\s*万人",
        note="宁夏日报电子版转载统计公报全文。",
    ),
    SourceSpec(
        province="新疆维吾尔自治区",
        source_id="SRC_CASE03_POP2024_R3_XJ",
        source_level="A",
        source_name="新疆维吾尔自治区人民政府-2024年国民经济和社会发展统计公报",
        source_url="https://www.xinjiang.gov.cn/xinjiang/tjgb/202503/f0578f74e4e04369af0ee82566586397.shtml",
        regex=r"年末全疆常住人口\s*([0-9]+(?:\.[0-9]+)?)\s*万人",
        note="2024统计公报正文口径。",
    ),
]


def normalize_text(txt: str) -> str:
    txt = re.sub(r"\s+", " ", txt or "")
    return txt


def fetch_text_requests(url: str) -> str:
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=35, verify=False)
    if r.status_code != 200:
        raise RuntimeError(f"status={r.status_code}")
    r.encoding = r.apparent_encoding or "utf-8"
    return normalize_text(BeautifulSoup(r.text, "html.parser").get_text(" "))


def fetch_text_camoufox(url: str) -> str:
    with Camoufox(headless=True, os="windows", humanize=True, locale=["zh-CN", "zh"]) as browser:
        ctx = browser.new_context()
        page = ctx.new_page()
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(1600)
        txt = page.inner_text("body")
        ctx.close()
    return normalize_text(txt)


def parse_value(text: str, regex: str) -> tuple[str, str]:
    m = re.search(regex, text)
    if not m:
        raise RuntimeError("regex_not_matched")
    value = m.group(1)
    i = m.start()
    evidence = text[max(0, i - 120) : i + 220]
    return value, evidence


def load_csv(path: Path) -> List[Dict]:
    with path.open("r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def save_csv(path: Path, rows: List[Dict], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    panel = load_csv(PANEL_PATH)
    registry = load_csv(REG_PATH)
    registry_ids = {r.get("source_id", "") for r in registry}
    today = date.today().isoformat()

    panel_map = {(r["province"], r["year"]): r for r in panel}
    evidence_rows: List[Dict] = []

    ok = 0
    skipped = 0
    failed = 0

    for spec in SPECS:
        key = (spec.province, "2024")
        row = panel_map.get(key)
        if row is None:
            failed += 1
            evidence_rows.append(
                {
                    "province": spec.province,
                    "year": "2024",
                    "status": "error",
                    "value_10k_person": "",
                    "source_url": spec.source_url,
                    "evidence": "",
                    "error": "panel_row_not_found",
                }
            )
            continue

        if (row.get("resident_population_10k_person") or "").strip():
            skipped += 1
            evidence_rows.append(
                {
                    "province": spec.province,
                    "year": "2024",
                    "status": "skipped_already_filled",
                    "value_10k_person": row.get("resident_population_10k_person", ""),
                    "source_url": row.get("source_url", ""),
                    "evidence": "",
                    "error": "",
                }
            )
            continue

        err = ""
        text = ""
        try:
            if spec.use_camoufox:
                text = fetch_text_camoufox(spec.source_url)
            else:
                try:
                    text = fetch_text_requests(spec.source_url)
                except Exception:
                    text = fetch_text_camoufox(spec.source_url)
            value, evidence = parse_value(text, spec.regex)
        except Exception as e:  # noqa: BLE001
            failed += 1
            err = str(e)
            evidence_rows.append(
                {
                    "province": spec.province,
                    "year": "2024",
                    "status": "error",
                    "value_10k_person": "",
                    "source_url": spec.source_url,
                    "evidence": "",
                    "error": err[:300],
                }
            )
            continue

        row["resident_population_10k_person"] = value
        row["source_id"] = spec.source_id
        row["source_level"] = spec.source_level
        row["source_name"] = spec.source_name
        row["source_url"] = spec.source_url
        row["publish_date"] = ""
        row["access_date"] = today
        row["evidence"] = evidence[:500]
        row["note"] = f"Round3严格补采; {spec.note}"

        if spec.source_id not in registry_ids:
            registry.append(
                {
                    "source_id": spec.source_id,
                    "variable": "resident_population_10k_person",
                    "source_level": spec.source_level,
                    "source_name": spec.source_name,
                    "source_url": spec.source_url,
                    "cross_check_url": "",
                    "publish_date": "",
                    "access_date": today,
                    "evidence_file": "population_2024_round3_evidence.csv",
                    "is_primary": "0",
                    "note": spec.note,
                }
            )
            registry_ids.add(spec.source_id)

        ok += 1
        evidence_rows.append(
            {
                "province": spec.province,
                "year": "2024",
                "status": "ok",
                "value_10k_person": value,
                "source_url": spec.source_url,
                "evidence": evidence[:500],
                "error": "",
            }
        )

    save_csv(
        PANEL_PATH,
        panel,
        [
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
    save_csv(
        REG_PATH,
        registry,
        [
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
    save_csv(
        EVIDENCE_PATH,
        evidence_rows,
        [
            "province",
            "year",
            "status",
            "value_10k_person",
            "source_url",
            "evidence",
            "error",
        ],
    )

    print(f"[DONE] ok={ok}, skipped={skipped}, failed={failed}")
    print(f"[DONE] panel={PANEL_PATH}")
    print(f"[DONE] registry={REG_PATH}")
    print(f"[DONE] evidence={EVIDENCE_PATH}")


if __name__ == "__main__":
    main()
