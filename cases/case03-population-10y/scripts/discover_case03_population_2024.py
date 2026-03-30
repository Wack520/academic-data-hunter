#!/usr/bin/env python3
"""
Case03：2024 年末常住人口候选来源发现（官方站点优先）。

输出：
- 每省搜索候选 URL
- 句级别常住人口候选值（万人）

增强：支持省份并发（--province-workers）与多引擎合并（--engine-mode merge）。
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import json
import os
import random
import re
import threading
import time
import tomllib
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from camoufox.sync_api import Camoufox

ROOT = Path(__file__).resolve().parents[3]
CASE_DIR = ROOT / "cases" / "case03-population-10y"
DATA_DIR = CASE_DIR / "data"
PANEL_PATH = DATA_DIR / "population_by_province.csv"
DEFAULT_OUT = CASE_DIR / "tmp" / "population_2024_candidates.json"
DEFAULT_ADDON = ROOT / "addons" / "fp_obfuscator_lite"

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

SUPPORTED_ENGINES = ("sogou", "360", "bing", "google", "tavily")
ENGINE_BONUS = {
    "google": 2,
    "tavily": 2,
    "bing": 1,
    "sogou": 1,
    "360": 1,
}

PROV_ALIAS = {
    "北京市": ["北京", "全市", "本市", "我市"],
    "天津市": ["天津", "全市", "本市", "我市"],
    "河北省": ["河北", "全省", "本省", "我省"],
    "山西省": ["山西", "全省", "本省", "我省"],
    "内蒙古自治区": ["内蒙古", "全区", "本区", "我区"],
    "辽宁省": ["辽宁", "全省", "本省", "我省"],
    "吉林省": ["吉林", "全省", "本省", "我省"],
    "黑龙江省": ["黑龙江", "全省", "本省", "我省"],
    "上海市": ["上海", "全市", "本市", "我市"],
    "江苏省": ["江苏", "全省", "本省", "我省"],
    "浙江省": ["浙江", "全省", "本省", "我省"],
    "安徽省": ["安徽", "全省", "本省", "我省"],
    "福建省": ["福建", "全省", "本省", "我省"],
    "江西省": ["江西", "全省", "本省", "我省"],
    "山东省": ["山东", "全省", "本省", "我省"],
    "河南省": ["河南", "全省", "本省", "我省"],
    "湖北省": ["湖北", "全省", "本省", "我省"],
    "湖南省": ["湖南", "全省", "本省", "我省"],
    "广东省": ["广东", "全省", "本省", "我省"],
    "广西壮族自治区": ["广西", "全区", "本区", "我区"],
    "海南省": ["海南", "全省", "本省", "我省"],
    "重庆市": ["重庆", "全市", "本市", "我市"],
    "四川省": ["四川", "全省", "本省", "我省"],
    "贵州省": ["贵州", "全省", "本省", "我省"],
    "云南省": ["云南", "全省", "本省", "我省"],
    "陕西省": ["陕西", "全省", "本省", "我省"],
    "甘肃省": ["甘肃", "全省", "本省", "我省"],
    "青海省": ["青海", "全省", "本省", "我省"],
    "宁夏回族自治区": ["宁夏", "全区", "本区", "我区"],
    "新疆维吾尔自治区": ["新疆", "全区", "本区", "我区"],
}

PROV_URL_HINTS = {
    "北京市": ["beijing", "bj"],
    "天津市": ["tianjin", "tj"],
    "河北省": ["hebei", "hb"],
    "山西省": ["shanxi", "sx"],
    "内蒙古自治区": ["nmg", "neimenggu"],
    "辽宁省": ["liaoning", "ln"],
    "吉林省": ["jilin", "jl"],
    "黑龙江省": ["heilongjiang", "hlj"],
    "上海市": ["shanghai", "sh"],
    "江苏省": ["jiangsu", "js"],
    "浙江省": ["zhejiang", "zj"],
    "安徽省": ["anhui", "ah"],
    "福建省": ["fujian", "fj"],
    "江西省": ["jiangxi", "jx"],
    "山东省": ["shandong", "sd"],
    "河南省": ["henan", "ha"],
    "湖北省": ["hubei", "hb"],
    "湖南省": ["hunan", "hn"],
    "广东省": ["guangdong", "gd"],
    "广西壮族自治区": ["gx", "guangxi"],
    "海南省": ["hainan", "hi"],
    "重庆市": ["cq", "chongqing"],
    "四川省": ["sichuan", "sc"],
    "贵州省": ["guizhou", "gz"],
    "云南省": ["yunnan", "yn"],
    "陕西省": ["shaanxi", "sn"],
    "甘肃省": ["gansu", "gs"],
    "青海省": ["qinghai", "qh"],
    "宁夏回族自治区": ["ningxia", "nx"],
    "新疆维吾尔自治区": ["xinjiang", "xj"],
}

OTHER_PROV_HINTS = [
    "北京",
    "天津",
    "河北",
    "山西",
    "内蒙古",
    "辽宁",
    "吉林",
    "黑龙江",
    "上海",
    "江苏",
    "浙江",
    "安徽",
    "福建",
    "江西",
    "山东",
    "河南",
    "湖北",
    "湖南",
    "广东",
    "广西",
    "海南",
    "重庆",
    "四川",
    "贵州",
    "云南",
    "陕西",
    "甘肃",
    "青海",
    "宁夏",
    "新疆",
]

PAGE_TEXT_CACHE: dict[str, str] = {}
PAGE_ERR_CACHE: dict[str, str] = {}
PAGE_CACHE_LOCK = threading.Lock()


def load_config_defaults(path: str) -> dict[str, Any]:
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"config not found: {p}")
    if p.suffix.lower() == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
    else:
        data = tomllib.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("config root must be object/table")
    cfg = data.get("discover", data)
    if not isinstance(cfg, dict):
        raise ValueError("config.discover must be object/table")
    return dict(cfg)


def parse_args() -> argparse.Namespace:
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--config", default="", help="可选：JSON/TOML 配置文件")
    pre_known, _ = pre.parse_known_args()
    cfg_defaults = load_config_defaults(pre_known.config) if pre_known.config else {}

    p = argparse.ArgumentParser(description="Case03 2024 常住人口候选发现")
    p.set_defaults(**cfg_defaults)
    p.add_argument("--config", default=pre_known.config, help="可选：JSON/TOML 配置文件")
    p.add_argument("--year", type=int, default=2024)
    p.add_argument("--provinces", default="", help="手工指定省份，逗号分隔；留空则自动读取该年缺失省份")
    p.add_argument("--max-pages", type=int, default=25)
    p.add_argument("--max-fetch-pages", type=int, default=15)
    p.add_argument("--run-mode", choices=["headless", "headed", "virtual"], default="headless")
    p.add_argument("--headless", action="store_true")
    p.add_argument("--delay-min-ms", type=int, default=700)
    p.add_argument("--delay-max-ms", type=int, default=1600)
    p.add_argument("--output", default=str(DEFAULT_OUT))
    p.add_argument("--addon-path", default=str(DEFAULT_ADDON))
    p.add_argument("--engines", default="google,tavily,bing,sogou,360")
    p.add_argument("--domain-filter", default="gov.cn")
    p.add_argument("--google-max-results", type=int, default=15)
    p.add_argument("--google-hl", default="zh-CN")
    p.add_argument("--google-gl", default="")
    p.add_argument("--tavily-api-key", default="")
    p.add_argument("--tavily-endpoint", default="https://api.tavily.com/search")
    p.add_argument("--tavily-max-results", type=int, default=10)
    p.add_argument("--tavily-topic", default="general")
    p.add_argument("--fetch-workers", type=int, default=8)
    p.add_argument("--province-workers", type=int, default=1, help="省份并发worker数（每个worker独立浏览器）")
    p.add_argument(
        "--engine-mode",
        choices=["first", "merge"],
        default="merge",
        help="搜索引擎模式：first=首个命中即返回；merge=合并多引擎结果（默认）",
    )
    p.add_argument("--per-domain-cap", type=int, default=3, help="每省同域名最多保留URL数（0为不限制）")
    p.add_argument("--request-timeout-sec", type=int, default=18)
    p.add_argument("--query-timeout-ms", type=int, default=45000)
    p.add_argument("--max-candidates", type=int, default=12)
    p.add_argument("--resume", action="store_true")
    p.add_argument("--force", action="store_true")
    args = p.parse_args()
    if not args.tavily_api_key:
        args.tavily_api_key = os.environ.get("TAVILY_API_KEY") or os.environ.get("TAVILY_KEY") or ""
    args.fetch_workers = max(1, int(args.fetch_workers))
    args.province_workers = max(1, int(args.province_workers))
    args.per_domain_cap = max(0, int(args.per_domain_cap))
    return args


def resolve_headless_mode(args: argparse.Namespace):
    if getattr(args, "headless", False):
        return True
    if args.run_mode == "headless":
        return True
    if args.run_mode == "virtual":
        return "virtual"
    return False


def parse_engines(raw: str) -> list[str]:
    arr = [x.strip().lower() for x in (raw or "").split(",") if x.strip()]
    if not arr:
        return ["google", "tavily", "bing", "sogou", "360"]
    bad = [x for x in arr if x not in SUPPORTED_ENGINES]
    if bad:
        raise ValueError(f"unsupported engines: {bad}, supported={SUPPORTED_ENGINES}")
    return arr


def parse_domain_filter(raw: str) -> list[str]:
    return [x.strip().lower() for x in (raw or "").split(",") if x.strip()]


def extract_domain(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


def score_domain_quality(url: str) -> int:
    host = extract_domain(url)
    if not host:
        return 0
    score = 0
    if host.endswith(".gov.cn") or ".gov.cn" in host:
        score += 6
    if any(k in host for k in ["stats", "tjj", "gov"]):
        score += 2
    if any(k in host for k in ["weixin.qq.com", "toutiao", "sohu", "163.com", "baijiahao"]):
        score -= 3
    return score


def cap_urls_by_domain(rows: list[dict], max_pages: int, per_domain_cap: int) -> list[dict]:
    if max_pages <= 0:
        return []
    if per_domain_cap <= 0:
        return rows[:max_pages]
    selected: list[dict] = []
    skipped: list[dict] = []
    domain_counter: dict[str, int] = defaultdict(int)
    for row in rows:
        domain = extract_domain(row.get("url", ""))
        if domain and domain_counter[domain] >= per_domain_cap:
            skipped.append(row)
            continue
        selected.append(row)
        if domain:
            domain_counter[domain] += 1
        if len(selected) >= max_pages:
            return selected
    if len(selected) >= max_pages:
        return selected[:max_pages]
    for row in skipped:
        selected.append(row)
        if len(selected) >= max_pages:
            break
    return selected


def load_missing_provinces(year: int) -> list[str]:
    rows = list(csv.DictReader(PANEL_PATH.open("r", encoding="utf-8-sig")))
    rows = [x for x in rows if (x.get("year") or "").strip() == str(year)]
    miss = sorted([x["province"] for x in rows if not (x.get("resident_population_10k_person") or "").strip()])
    return miss


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text)
    arr = re.split(r"(?<=[。！？；])", text)
    return [x.strip() for x in arr if x.strip()]


def fetch_text(url: str, retries: int = 2, timeout_sec: int = 18) -> str:
    last_err: Exception | None = None
    for _ in range(retries + 1):
        try:
            r = requests.get(url, headers=UA, timeout=timeout_sec)
            if r.status_code != 200:
                raise RuntimeError(f"status={r.status_code}")
            r.encoding = r.apparent_encoding or "utf-8"
            txt = BeautifulSoup(r.text, "html.parser").get_text(" ")
            txt = re.sub(r"\s+", " ", txt)
            return txt
        except Exception as e:
            last_err = e
            time.sleep(0.4)
    raise RuntimeError(f"fetch failed: {url}, err={last_err}")


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_existing_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def extract_candidates(province: str, url: str, text: str, year: int) -> list[dict]:
    alias = PROV_ALIAS.get(province, [province.replace("省", "").replace("市", "")])
    explicit_name = alias[0]
    url_l = url.lower()
    out: list[dict] = []
    for sent in split_sentences(text):
        if "常住人口" not in sent:
            continue
        if "全国" in sent and explicit_name not in sent and province not in sent:
            continue
        has_explicit_prov = explicit_name in sent or province in sent
        has_generic_scope = any(a in sent for a in alias[1:])
        if not (has_explicit_prov or has_generic_scope):
            continue
        if not has_explicit_prov:
            hints = PROV_URL_HINTS.get(province, [])
            if hints and not any(h in url_l for h in hints):
                continue

        m = re.search(r"(?:年末常住人口|常住人口)(?:总量)?(?:达|达到|为|有)?\s*([0-9]+(?:\.[0-9]+)?)\s*万人", sent)
        if not m:
            m = re.search(r"(?:常住人口)[^。；，,]{0,40}([0-9]+(?:\.[0-9]+)?)\s*万人", sent)
        if not m:
            continue

        val = float(m.group(1))
        score = 0
        if any(k in sent for k in [f"{year}年末", f"截至{year}年末", f"{year}年"]):
            score += 8
        if "统计公报" in sent or "国民经济和社会发展" in sent:
            score += 4
        if any(k in sent for k in ["全省", "全区", "全市", "我省", "我区", "我市"]):
            score += 4
        if has_explicit_prov:
            score += 4
        if "全国" in sent:
            score -= 10
        for prov_kw in OTHER_PROV_HINTS:
            if prov_kw == explicit_name:
                continue
            if prov_kw in sent:
                score -= 8
                break

        out.append(
            {
                "url": url,
                "sentence": sent[:260],
                "value_10k_person": round(val, 6),
                "unit": "万人",
                "score": score,
                "explicit_province_in_sentence": has_explicit_prov,
            }
        )
    return out


def dedup_candidates(cands: list[dict]) -> list[dict]:
    dedup = []
    used = set()
    for c in sorted(cands, key=lambda x: x["score"], reverse=True):
        k = (c["url"], c["value_10k_person"], c["sentence"])
        if k in used:
            continue
        used.add(k)
        dedup.append(c)
    return dedup


def build_queries(prov: str, year: int) -> list[str]:
    y = str(year)
    return [
        f"{prov} {y}年末常住人口 万人 site:gov.cn",
        f"{prov} {y} 国民经济和社会发展统计公报 常住人口 site:gov.cn",
        f"{prov} {y} 统计公报 常住人口 万人 site:gov.cn",
        f"{prov} 常住人口 {y} 统计局 site:gov.cn",
    ]


def score_search_row(province: str, year: int, row: dict) -> int:
    txt = f"{row.get('title', '')} {row.get('snippet', '')}"
    score = 0
    short = PROV_ALIAS.get(province, [province.replace("省", "").replace("市", "")])[0]
    if short in txt or province in txt:
        score += 4
    if "常住人口" in txt:
        score += 5
    if str(year) in txt:
        score += 4
    if "统计公报" in txt:
        score += 3
    if "统计局" in txt or "政府" in txt or "国民经济和社会发展" in txt:
        score += 2
    if "全国" in txt:
        score -= 4
    return score


def search_urls_with_sogou(page, query: str) -> tuple[bool, list[dict]]:
    url = "https://www.sogou.com/web?query=" + requests.utils.quote(query)
    page.goto(url, timeout=45000, wait_until="domcontentloaded")
    page.wait_for_timeout(random.randint(1200, 2000))
    anti = "/antispider/" in page.url
    rows = page.evaluate(
        """() => {
            const out = [];
            const blocks = Array.from(document.querySelectorAll('.vrwrap'));
            for (const b of blocks) {
                const a = b.querySelector('h3 a, h4 a, a');
                const title = (a?.innerText || '').replace(/\\s+/g, ' ').trim();
                const dataUrl = b.querySelector('[data-url]')?.getAttribute('data-url') || '';
                const snippet = (b.innerText || '').replace(/\\s+/g, ' ').trim();
                if (title && dataUrl) out.push({title, data_url: dataUrl, snippet});
            }
            return out.slice(0, 20);
        }"""
    )
    return anti, rows


def search_urls_with_bing(page, query: str) -> list[dict]:
    url = "https://www.bing.com/search?q=" + requests.utils.quote(query)
    page.goto(url, timeout=45000, wait_until="domcontentloaded")
    page.wait_for_timeout(random.randint(900, 1600))
    rows = page.evaluate(
        """() => {
            const out = [];
            const items = Array.from(document.querySelectorAll('li.b_algo'));
            for (const li of items) {
                const a = li.querySelector('h2 a');
                const href = a?.getAttribute('href') || '';
                const title = (a?.innerText || '').replace(/\\s+/g, ' ').trim();
                const snippet = (li.innerText || '').replace(/\\s+/g, ' ').trim();
                if (href && title) out.push({title, data_url: href, snippet});
            }
            return out.slice(0, 15);
        }"""
    )
    return rows


def search_urls_with_google(
    page, query: str, max_results: int = 15, hl: str = "zh-CN", gl: str = ""
) -> tuple[bool, list[dict]]:
    q = requests.utils.quote(query)
    url = f"https://www.google.com/search?q={q}&num={max(1, min(max_results, 50))}&hl={hl}"
    if gl:
        url += f"&gl={gl}"
    page.goto(url, timeout=45000, wait_until="domcontentloaded")
    page.wait_for_timeout(random.randint(900, 1600))
    anti = "/sorry/" in page.url
    rows = page.evaluate(
        """() => {
            const out = [];
            const anchors = Array.from(document.querySelectorAll('div#search a'));
            for (const a of anchors) {
                const href = a.getAttribute('href') || '';
                const h3 = a.querySelector('h3');
                const title = (h3?.innerText || a.innerText || '').replace(/\\s+/g, ' ').trim();
                if (!href || !title) continue;
                if (href.startsWith('/')) continue;
                if (!/^https?:\\/\\//.test(href)) continue;
                const card = a.closest('div.g, div.MjjYud, div.tF2Cxc') || a.parentElement;
                const snippet = (card?.innerText || '').replace(/\\s+/g, ' ').trim();
                out.push({title, data_url: href, snippet});
            }
            return out.slice(0, 30);
        }"""
    )
    return anti, rows


def search_urls_with_tavily(
    query: str,
    api_key: str,
    endpoint: str,
    max_results: int = 10,
    topic: str = "general",
) -> list[dict]:
    if not api_key:
        return []
    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "advanced",
        "max_results": max(1, min(int(max_results), 20)),
        "topic": topic or "general",
        "include_answer": False,
        "include_images": False,
        "include_raw_content": False,
    }
    r = requests.post(endpoint, json=payload, timeout=25)
    if r.status_code != 200:
        return []
    data = r.json()
    arr = data.get("results", []) if isinstance(data, dict) else []
    out: list[dict] = []
    for it in arr:
        if not isinstance(it, dict):
            continue
        u = (it.get("url") or "").strip()
        title = (it.get("title") or "").strip()
        snippet = (it.get("content") or "").strip()
        if u and title:
            out.append({"title": title, "data_url": u, "snippet": snippet})
    return out


def search_urls_with_360(page, query: str) -> tuple[bool, list[dict]]:
    url = "https://www.so.com/s?q=" + requests.utils.quote(query)
    page.goto(url, timeout=45000, wait_until="domcontentloaded")
    page.wait_for_timeout(random.randint(900, 1500))
    anti = "qcaptcha.so.com" in page.url
    if anti:
        return True, []
    rows = page.evaluate(
        """() => {
            const out = [];
            const items = Array.from(document.querySelectorAll('h3.res-title a'));
            for (const a of items) {
                const title = (a.innerText || '').replace(/\\s+/g, ' ').trim();
                const dataUrl = a.getAttribute('data-mdurl') || a.getAttribute('href') || '';
                if (title && dataUrl) out.push({title, data_url: dataUrl, snippet: title});
            }
            return out.slice(0, 20);
        }"""
    )
    return False, rows


def run_single_query(page, query: str, engines: list[str], args: argparse.Namespace) -> tuple[list[dict], dict]:
    anti_stats = {"sogou": False, "360": False, "google": False}
    all_rows: list[dict] = []
    hit_engines: list[str] = []
    errors: list[dict[str, str]] = []
    for engine in engines:
        try:
            rows: list[dict] = []
            if engine == "sogou":
                anti, rows = search_urls_with_sogou(page, query)
                anti_stats["sogou"] = anti
            elif engine == "360":
                anti, rows = search_urls_with_360(page, query)
                anti_stats["360"] = anti
            elif engine == "bing":
                rows = search_urls_with_bing(page, query)
            elif engine == "google":
                anti, rows = search_urls_with_google(
                    page, query, max_results=int(args.google_max_results), hl=args.google_hl, gl=args.google_gl
                )
                anti_stats["google"] = anti
            elif engine == "tavily":
                rows = search_urls_with_tavily(
                    query,
                    api_key=args.tavily_api_key,
                    endpoint=args.tavily_endpoint,
                    max_results=int(args.tavily_max_results),
                    topic=args.tavily_topic,
                )
            else:
                rows = []
            if rows:
                hit_engines.append(engine)
                for row in rows:
                    item = dict(row)
                    item["engine"] = engine
                    all_rows.append(item)
                if args.engine_mode == "first":
                    break
        except Exception as e:
            errors.append({"engine": engine, "error": str(e)[:180]})
            continue
    dedup_by_url: dict[str, dict] = {}
    order = 0
    for row in all_rows:
        u = (row.get("data_url") or "").strip()
        if not u:
            continue
        prev = dedup_by_url.get(u)
        row["_order"] = order
        order += 1
        if prev is None:
            dedup_by_url[u] = row
            continue
        prev_len = len(prev.get("title") or "") + len(prev.get("snippet") or "")
        cur_len = len(row.get("title") or "") + len(row.get("snippet") or "")
        if cur_len > prev_len:
            row["_order"] = int(prev.get("_order", row["_order"]))
            dedup_by_url[u] = row

    rows_final = sorted(dedup_by_url.values(), key=lambda x: int(x.get("_order", 0)))
    for row in rows_final:
        row.pop("_order", None)
    used_engine_str = ""
    if hit_engines:
        used_engine_str = hit_engines[0] if len(hit_engines) == 1 else ",".join(hit_engines)
    return rows_final, {
        "engine": used_engine_str,
        "engines_hit": hit_engines,
        "anti_sogou": anti_stats["sogou"],
        "anti_360": anti_stats["360"],
        "anti_google": anti_stats["google"],
        "errors": errors[:5],
    }


def scan_url_for_candidates(province: str, url: str, year: int, timeout_sec: int) -> list[dict]:
    with PAGE_CACHE_LOCK:
        if url in PAGE_TEXT_CACHE:
            return extract_candidates(province, url, PAGE_TEXT_CACHE[url], year)
        if url in PAGE_ERR_CACHE:
            raise RuntimeError(PAGE_ERR_CACHE[url])
    try:
        txt = fetch_text(url, timeout_sec=timeout_sec)
        with PAGE_CACHE_LOCK:
            PAGE_TEXT_CACHE[url] = txt
        return extract_candidates(province, url, txt, year)
    except Exception as e:
        with PAGE_CACHE_LOCK:
            PAGE_ERR_CACHE[url] = str(e)
        raise


def process_single_province(
    browser, prov: str, args: argparse.Namespace, engines: list[str], max_fetch_pages: int, domain_filters: list[str]
) -> dict:
    queries = build_queries(prov, args.year)
    query_debug: list[dict] = []
    anti_count = 0
    urls: list[str] = []

    ctx = browser.new_context()
    page = ctx.new_page()
    page.set_default_timeout(int(args.query_timeout_ms))
    try:
        url_rows: dict[str, dict] = {}
        for q in queries:
            try:
                rows, dbg = run_single_query(page, q, engines, args)
            except Exception as e:
                query_debug.append({"query": q, "error": str(e)[:180]})
                if "Target page" in str(e) or "browser has been closed" in str(e):
                    break
                continue
            if dbg.get("anti_sogou"):
                anti_count += 1
            if dbg.get("anti_360"):
                anti_count += 1
            if dbg.get("anti_google"):
                anti_count += 1
            for r in rows:
                u = (r.get("data_url") or "").strip()
                if not (u.startswith("http://") or u.startswith("https://")):
                    continue
                u_l = u.lower()
                if domain_filters and (not any(x in u_l for x in domain_filters)):
                    continue
                row_engine = (r.get("engine") or dbg.get("engine") or "").split(",")[0]
                row_score = score_search_row(prov, args.year, r)
                domain_score = score_domain_quality(u)
                row_score += domain_score
                row_score += int(ENGINE_BONUS.get(row_engine, 0))
                prev = url_rows.get(u)
                if (prev is None) or (row_score > int(prev.get("search_score", -999))):
                    url_rows[u] = {
                        "url": u,
                        "title": (r.get("title") or "").strip(),
                        "snippet": (r.get("snippet") or "").strip(),
                        "query": q,
                        "engine": row_engine or dbg.get("engine", ""),
                        "search_score": row_score,
                        "domain_score": domain_score,
                    }
            query_debug.append(
                {
                    "query": q,
                    "engine": dbg.get("engine", ""),
                    "engines_hit": dbg.get("engines_hit", []),
                    "row_count": len(rows),
                    "anti_sogou": bool(dbg.get("anti_sogou")),
                    "anti_360": bool(dbg.get("anti_360")),
                    "anti_google": bool(dbg.get("anti_google")),
                    "errors": dbg.get("errors", []),
                }
            )
            try:
                page.wait_for_timeout(random.randint(args.delay_min_ms, args.delay_max_ms))
            except Exception as e:
                query_debug.append({"query": q, "wait_error": str(e)[:180]})
                if "Target page" in str(e) or "browser has been closed" in str(e):
                    break
        ranked = sorted(url_rows.values(), key=lambda x: int(x.get("search_score", 0)), reverse=True)
        selected = cap_urls_by_domain(
            ranked,
            max_pages=int(args.max_pages),
            per_domain_cap=int(args.per_domain_cap),
        )
        fetch_targets = selected[:max_fetch_pages]
        urls = [x["url"] for x in selected]
    finally:
        with contextlib.suppress(Exception):
            ctx.close()

    cands: list[dict] = []
    with ThreadPoolExecutor(max_workers=max(1, int(args.fetch_workers))) as ex:
        futures = {
            ex.submit(scan_url_for_candidates, prov, item["url"], int(args.year), int(args.request_timeout_sec)): item
            for item in fetch_targets
        }
        for fut in as_completed(futures):
            meta = futures[fut]
            try:
                got = fut.result()
                for c in got:
                    c["search_score"] = meta.get("search_score", 0)
                    c["search_title"] = meta.get("title", "")[:120]
                    c["search_query"] = meta.get("query", "")
                    c["search_engine"] = meta.get("engine", "")
                cands.extend(got)
            except Exception:
                continue

    dedup = dedup_candidates(cands)
    top_n = dedup[: max(1, int(args.max_candidates))]
    return {
        "finished": True,
        "searched_at": datetime.now().isoformat(timespec="seconds"),
        "engines": engines,
        "engine_mode": args.engine_mode,
        "per_domain_cap": int(args.per_domain_cap),
        "queries": query_debug,
        "anti_spider_hits": anti_count,
        "url_count_raw": len(url_rows),
        "url_count": len(urls),
        "fetch_count": len(fetch_targets),
        "selected_urls": [x.get("url", "") for x in selected if x.get("url")][:100],
        "selected_url_meta": [
            {
                "url": x.get("url", ""),
                "search_score": x.get("search_score", 0),
                "engine": x.get("engine", ""),
                "query": x.get("query", ""),
                "title": x.get("title", "")[:120],
            }
            for x in selected[:60]
        ],
        "candidate_count": len(dedup),
        "top_candidates": top_n,
    }


def main() -> None:
    args = parse_args()
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    engines = parse_engines(args.engines)
    domain_filters = parse_domain_filter(args.domain_filter)

    if args.provinces.strip():
        provinces = [x.strip() for x in args.provinces.split(",") if x.strip()]
    else:
        provinces = load_missing_provinces(args.year)
    if not provinces:
        print("[INFO] no provinces to process")
        return

    result: dict[str, dict] = load_existing_json(out_path) if args.resume else {}
    to_run: list[str] = []
    for prov in provinces:
        if args.force:
            to_run.append(prov)
            continue
        prev = result.get(prov) if isinstance(result, dict) else None
        if prev and prev.get("finished"):
            print(f"[SKIP] {prov} (resume hit)")
            continue
        to_run.append(prov)
    if not to_run:
        print("[INFO] all target provinces are already completed in output file")
        return

    addon_paths = []
    addon_dir = Path(args.addon_path)
    if addon_dir.exists() and (addon_dir / "manifest.json").exists():
        addon_paths.append(str(addon_dir))

    headless_mode = resolve_headless_mode(args)
    firefox_user_prefs = {
        "dom.min_background_timeout_value": 0,
        "dom.timeout.enable_budget_timer_throttling": False,
        "dom.timeout.background_throttling_max_budget": -1,
        "dom.timeout.background_throttling_max_delay": 0,
        "browser.tabs.unloadOnLowMemory": False,
    }

    max_fetch_pages = max(1, min(int(args.max_fetch_pages), int(args.max_pages)))
    print(
        f"[INFO] provinces={len(to_run)}, engines={engines}, engine_mode={args.engine_mode}, "
        f"fetch_workers={args.fetch_workers}, province_workers={args.province_workers}, "
        f"max_pages={args.max_pages}, max_fetch_pages={max_fetch_pages}, "
        f"per_domain_cap={args.per_domain_cap}, domain_filter={domain_filters or 'ALL'}"
    )

    def open_browser():
        return Camoufox(
            headless=headless_mode,
            os="windows",
            humanize=True,
            locale=["zh-CN", "zh"],
            addons=addon_paths,
            firefox_user_prefs=firefox_user_prefs,
        )

    result_lock = threading.Lock()

    def save_prov_result(prov_name: str, rec: dict) -> None:
        with result_lock:
            result[prov_name] = rec
            save_json(out_path, result)

    def worker_loop(worker_id: int, prov_list: list[str]) -> None:
        if not prov_list:
            return
        worker_tag = f"W{worker_id}"
        browser_cm = open_browser()
        browser = browser_cm.__enter__()
        try:
            for prov in prov_list:
                print(f"[RUN][{worker_tag}] {prov}")
                retried = 0
                while True:
                    try:
                        rec = process_single_province(browser, prov, args, engines, max_fetch_pages, domain_filters)
                        rec["worker"] = worker_tag
                        save_prov_result(prov, rec)
                        print(
                            f"  [OK][{worker_tag}] urls_raw={rec.get('url_count_raw', 0)} "
                            f"selected={rec.get('url_count', 0)} fetch={rec.get('fetch_count', 0)} "
                            f"anti={rec.get('anti_spider_hits', 0)} candidates={rec.get('candidate_count', 0)}"
                        )
                        break
                    except Exception as e:
                        msg = str(e)
                        recoverable = "Target page" in msg or "browser has been closed" in msg
                        if recoverable and retried < 2:
                            retried += 1
                            print(f"  [WARN][{worker_tag}] browser crashed, restart and retry ({retried}/2)")
                            with contextlib.suppress(Exception):
                                browser_cm.__exit__(None, None, None)
                            browser_cm = open_browser()
                            browser = browser_cm.__enter__()
                            continue
                        save_prov_result(
                            prov,
                            {
                                "finished": False,
                                "searched_at": datetime.now().isoformat(timespec="seconds"),
                                "error": msg[:300],
                                "worker": worker_tag,
                            },
                        )
                        print(f"  [ERR][{worker_tag}] {prov}: {msg}")
                        break
        finally:
            with contextlib.suppress(Exception):
                browser_cm.__exit__(None, None, None)

    province_workers = max(1, min(int(args.province_workers), len(to_run)))
    if province_workers <= 1:
        worker_loop(1, to_run)
    else:
        buckets: list[list[str]] = [[] for _ in range(province_workers)]
        for idx, prov in enumerate(to_run):
            buckets[idx % province_workers].append(prov)
        with ThreadPoolExecutor(max_workers=province_workers) as ex:
            futures = [ex.submit(worker_loop, i + 1, buckets[i]) for i in range(province_workers) if buckets[i]]
            for fut in as_completed(futures):
                fut.result()

    save_json(out_path, result)
    print(f"[DONE] saved: {out_path}")


if __name__ == "__main__":
    main()
