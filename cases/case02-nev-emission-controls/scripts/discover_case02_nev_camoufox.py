#!/usr/bin/env python3
"""
使用 Camoufox 批量搜索 Case02 严格口径 NEV 缺失省份候选来源（增强版）。

改进点：
- 单次运行自动处理全部目标省份（无需多次人工交互）
- 浏览器单实例复用（减少启动开销）
- 支持断点续跑（--resume）
- 支持可配置搜索引擎顺序（--engines）
- URL 文本抓取并发（--fetch-workers）
- 省份级并发（--province-workers）
- 多引擎结果合并召回（--engine-mode merge）
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import json
import logging
import os
import random
import threading
import tomllib
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from camoufox.sync_api import Camoufox

from tools.candidate_extractor import dedup, extract_candidates, score_domain_quality, score_search_result
from tools.engines import get_engine, supported_engines
from tools.fetcher import get_or_fetch_text

ROOT = Path(__file__).resolve().parents[3]
CASE_DIR = ROOT / "cases" / "case02-nev-emission-controls"
DATA_DIR = CASE_DIR / "data"
PANEL_PATH = DATA_DIR / "panel_case02_strict_30prov_2012_2023.csv"
DEFAULT_OUT = CASE_DIR / "tmp" / "camoufox_nev_candidates_2023.json"
DEFAULT_ADDON = ROOT / "addons" / "fp_obfuscator_lite"

SUPPORTED_ENGINES = supported_engines()
ENGINE_BONUS = {
    "google": 2,
    "tavily": 2,
    "bing": 1,
    "sogou": 1,
    "360": 1,
}


def load_config_defaults(path: str) -> dict[str, Any]:
    if not path:
        return {}
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"config not found: {config_path}")
    if config_path.suffix.lower() == ".json":
        data = json.loads(config_path.read_text(encoding="utf-8"))
    else:
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("config root must be object/table")
    config_data = data.get("discover", data)
    if not isinstance(config_data, dict):
        raise ValueError("config.discover must be object/table")
    return dict(config_data)


def parse_args() -> argparse.Namespace:
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--config", default="", help="可选：JSON/TOML 配置文件")
    pre_known, _ = pre.parse_known_args()
    cfg_defaults = load_config_defaults(pre_known.config) if pre_known.config else {}

    parser = argparse.ArgumentParser(description="Camoufox 批量搜索 NEV 严格口径候选来源（增强版）")
    parser.set_defaults(**cfg_defaults)
    parser.add_argument("--config", default=pre_known.config, help="可选：JSON/TOML 配置文件")
    parser.add_argument("--year", type=int, default=2023, help="目标年份（默认 2023）")
    parser.add_argument(
        "--provinces",
        default="",
        help="手工指定省份，逗号分隔；留空则自动读取 strict 面板中该年份缺失省份",
    )
    parser.add_argument("--max-pages", type=int, default=30, help="每省最多抓取候选 URL 数")
    parser.add_argument(
        "--max-fetch-pages",
        type=int,
        default=20,
        help="每省实际抓取正文的 URL 数（<= max-pages，默认20，提速）",
    )
    parser.add_argument(
        "--run-mode",
        choices=["headless", "headed", "virtual"],
        default="headless",
        help="浏览器模式：headless(默认) / headed / virtual",
    )
    parser.add_argument("--headless", action="store_true", help="兼容参数：等价于 --run-mode headless")
    parser.add_argument("--delay-min-ms", type=int, default=1000, help="查询间最小等待毫秒")
    parser.add_argument("--delay-max-ms", type=int, default=2200, help="查询间最大等待毫秒")
    parser.add_argument("--output", default=str(DEFAULT_OUT), help="输出 JSON 路径")
    parser.add_argument(
        "--addon-path",
        default=str(DEFAULT_ADDON),
        help="指纹混淆插件目录（Firefox unpacked addon）",
    )
    parser.add_argument(
        "--engines",
        default="google,tavily,bing,sogou,360",
        help="搜索引擎顺序，逗号分隔，可选：sogou,360,bing,google,tavily",
    )
    parser.add_argument(
        "--domain-filter",
        default="gov.cn",
        help="URL域名白名单（逗号分隔，空字符串表示不做域名过滤）",
    )
    parser.add_argument("--google-max-results", type=int, default=15, help="Google 每次query最大结果数")
    parser.add_argument("--google-hl", default="zh-CN", help="Google 语言参数 hl")
    parser.add_argument("--google-gl", default="", help="Google 地区参数 gl（可空）")
    parser.add_argument("--tavily-api-key", default="", help="Tavily API Key（可用环境变量 TAVILY_API_KEY）")
    parser.add_argument("--tavily-endpoint", default="https://api.tavily.com/search", help="Tavily 搜索接口")
    parser.add_argument("--tavily-max-results", type=int, default=10, help="Tavily 每次query返回上限")
    parser.add_argument("--tavily-topic", default="general", help="Tavily topic: general/news")
    parser.add_argument("--fetch-workers", type=int, default=8, help="抓取候选URL正文的并发线程数")
    parser.add_argument(
        "--province-workers",
        type=int,
        default=1,
        help="省份并发worker数（每个worker独立浏览器，默认1）",
    )
    parser.add_argument(
        "--engine-mode",
        choices=["first", "merge"],
        default="merge",
        help="搜索引擎模式：first=首个命中即返回；merge=合并多引擎结果（默认）",
    )
    parser.add_argument(
        "--per-domain-cap",
        type=int,
        default=3,
        help="每省同一域名最多保留URL数（0表示不限制）",
    )
    parser.add_argument("--request-timeout-sec", type=int, default=18, help="正文抓取请求超时秒数")
    parser.add_argument("--query-timeout-ms", type=int, default=45000, help="单次查询页面超时毫秒")
    parser.add_argument("--max-candidates", type=int, default=12, help="每省输出 top 候选数量")
    parser.add_argument("--resume", action="store_true", help="从已有输出断点续跑")
    parser.add_argument("--force", action="store_true", help="忽略断点信息，强制重跑")
    args = parser.parse_args()

    if not args.tavily_api_key:
        args.tavily_api_key = os.environ.get("TAVILY_API_KEY") or os.environ.get("TAVILY_KEY") or ""
    args.fetch_workers = max(1, int(args.fetch_workers))
    args.province_workers = max(1, int(args.province_workers))
    args.per_domain_cap = max(0, int(args.per_domain_cap))
    return args


def resolve_headless_mode(args: argparse.Namespace) -> bool | str:
    if getattr(args, "headless", False):
        return True
    if args.run_mode == "headless":
        return True
    if args.run_mode == "virtual":
        return "virtual"
    return False


def parse_engines(raw: str) -> list[str]:
    engines = [item.strip().lower() for item in (raw or "").split(",") if item.strip()]
    if not engines:
        return ["google", "tavily", "bing", "sogou", "360"]
    unknown = [item for item in engines if item not in SUPPORTED_ENGINES]
    if unknown:
        raise ValueError(f"unsupported engines: {unknown}, supported={SUPPORTED_ENGINES}")
    return engines


def parse_domain_filter(raw: str) -> list[str]:
    return [item.strip().lower() for item in (raw or "").split(",") if item.strip()]


def extract_domain(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


def cap_urls_by_domain(rows: list[dict[str, Any]], max_pages: int, per_domain_cap: int) -> list[dict[str, Any]]:
    if max_pages <= 0:
        return []
    if per_domain_cap <= 0:
        return rows[:max_pages]

    selected: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    domain_counter: dict[str, int] = defaultdict(int)
    for row in rows:
        domain = extract_domain(str(row.get("url", "")))
        if domain and domain_counter[domain] >= per_domain_cap:
            skipped.append(row)
            continue
        selected.append(row)
        if domain:
            domain_counter[domain] += 1
        if len(selected) >= max_pages:
            return selected

    if len(selected) < max_pages:
        for row in skipped:
            selected.append(row)
            if len(selected) >= max_pages:
                break

    return selected[:max_pages]


def load_missing_provinces(year: int) -> list[str]:
    rows = list(csv.DictReader(PANEL_PATH.open("r", encoding="utf-8-sig")))
    target_rows = [row for row in rows if (row.get("year") or "").strip() == str(year)]
    return sorted(row["province"] for row in target_rows if not (row.get("nev_stock_10k") or "").strip())


def save_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_existing_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def build_queries(province: str, year: int) -> list[str]:
    year_text = str(year)
    return [
        f"{province} 截至{year_text}年底 新能源汽车 保有量 site:gov.cn",
        f"{province} {year_text} 新能源汽车 保有量 site:gov.cn",
        f"{province} {year_text} 电动汽车 保有量 site:gov.cn",
        f"{province} 机动车 保有量 新能源汽车 site:gov.cn",
        f"{province} 交管 新能源汽车 保有量 site:gov.cn",
    ]


def _engine_kwargs(engine: str, args: argparse.Namespace) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"timeout_ms": int(args.query_timeout_ms)}
    if engine == "google":
        kwargs.update(
            {
                "max_results": int(args.google_max_results),
                "hl": args.google_hl,
                "gl": args.google_gl,
            }
        )
    elif engine == "tavily":
        kwargs.update(
            {
                "api_key": args.tavily_api_key,
                "endpoint": args.tavily_endpoint,
                "max_results": int(args.tavily_max_results),
                "topic": args.tavily_topic,
            }
        )
    return kwargs


def run_single_query(
    page: Any, query: str, engines: list[str], args: argparse.Namespace
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    anti_stats = {"sogou": False, "360": False, "google": False}
    all_rows: list[dict[str, Any]] = []
    hit_engines: list[str] = []
    errors: list[dict[str, str]] = []

    for engine_name in engines:
        try:
            engine = get_engine(engine_name)
            rows = engine.search(query, page, **_engine_kwargs(engine_name, args))
            meta = engine.get_last_meta()
            anti_stats["sogou"] = anti_stats["sogou"] or bool(meta.get("anti_sogou"))
            anti_stats["360"] = anti_stats["360"] or bool(meta.get("anti_360"))
            anti_stats["google"] = anti_stats["google"] or bool(meta.get("anti_google"))
            if rows:
                hit_engines.append(engine_name)
                all_rows.extend(
                    {
                        "title": result.title,
                        "data_url": result.url,
                        "snippet": result.snippet,
                        "engine": engine_name,
                    }
                    for result in rows
                )
                if args.engine_mode == "first":
                    break
        except Exception as exc:
            errors.append({"engine": engine_name, "error": str(exc)[:180]})

    dedup_by_url: dict[str, dict[str, Any]] = {}
    order = 0
    for row in all_rows:
        url = (row.get("data_url") or "").strip()
        if not url:
            continue
        previous = dedup_by_url.get(url)
        row["_order"] = order
        order += 1
        if previous is None:
            dedup_by_url[url] = row
            continue
        previous_len = len(previous.get("title") or "") + len(previous.get("snippet") or "")
        current_len = len(row.get("title") or "") + len(row.get("snippet") or "")
        if current_len > previous_len:
            row["_order"] = int(previous.get("_order", row["_order"]))
            dedup_by_url[url] = row

    rows_final = sorted(dedup_by_url.values(), key=lambda item: int(item.get("_order", 0)))
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


def scan_url_for_candidates(province: str, url: str, timeout_sec: int, year: int) -> list[dict[str, object]]:
    text = get_or_fetch_text(url, timeout_sec=timeout_sec)
    return extract_candidates(province, url, text, year=year)


def process_single_province(
    browser: Any,
    province: str,
    args: argparse.Namespace,
    engines: list[str],
    max_fetch_pages: int,
    domain_filters: list[str],
) -> dict[str, Any]:
    queries = build_queries(province, args.year)
    query_debug: list[dict[str, Any]] = []
    anti_count = 0
    url_rows: dict[str, dict[str, Any]] = {}

    context = browser.new_context()
    page = context.new_page()
    page.set_default_timeout(int(args.query_timeout_ms))
    try:
        for query in queries:
            try:
                rows, debug = run_single_query(page, query, engines, args)
            except Exception as exc:
                query_debug.append({"query": query, "error": str(exc)[:180]})
                if "Target page" in str(exc) or "browser has been closed" in str(exc):
                    break
                continue

            if debug.get("anti_sogou"):
                anti_count += 1
            if debug.get("anti_360"):
                anti_count += 1
            if debug.get("anti_google"):
                anti_count += 1

            for row in rows:
                url = (row.get("data_url") or "").strip()
                if not (url.startswith("http://") or url.startswith("https://")):
                    continue
                lower_url = url.lower()
                if domain_filters and not any(domain in lower_url for domain in domain_filters):
                    continue

                row_engine = (row.get("engine") or debug.get("engine") or "").split(",")[0]
                row_score = score_search_result(
                    province,
                    args.year,
                    str(row.get("title") or ""),
                    str(row.get("snippet") or ""),
                )
                domain_score = score_domain_quality(url)
                row_score += domain_score + int(ENGINE_BONUS.get(row_engine, 0))

                previous = url_rows.get(url)
                if previous is None or row_score > int(previous.get("search_score", -999)):
                    url_rows[url] = {
                        "url": url,
                        "title": (row.get("title") or "").strip(),
                        "snippet": (row.get("snippet") or "").strip(),
                        "query": query,
                        "engine": row_engine or debug.get("engine", ""),
                        "search_score": row_score,
                        "domain_score": domain_score,
                    }

            query_debug.append(
                {
                    "query": query,
                    "engine": debug.get("engine", ""),
                    "engines_hit": debug.get("engines_hit", []),
                    "row_count": len(rows),
                    "anti_sogou": bool(debug.get("anti_sogou")),
                    "anti_360": bool(debug.get("anti_360")),
                    "anti_google": bool(debug.get("anti_google")),
                    "errors": debug.get("errors", []),
                }
            )
            try:
                page.wait_for_timeout(random.randint(args.delay_min_ms, args.delay_max_ms))
            except Exception as exc:
                query_debug.append({"query": query, "wait_error": str(exc)[:180]})
                if "Target page" in str(exc) or "browser has been closed" in str(exc):
                    break
    finally:
        with contextlib.suppress(Exception):
            context.close()

    ranked = sorted(url_rows.values(), key=lambda item: int(item.get("search_score", 0)), reverse=True)
    selected = cap_urls_by_domain(ranked, max_pages=int(args.max_pages), per_domain_cap=int(args.per_domain_cap))
    fetch_targets = selected[:max_fetch_pages]

    candidates: list[dict[str, object]] = []
    with ThreadPoolExecutor(max_workers=max(1, int(args.fetch_workers))) as executor:
        futures = {
            executor.submit(
                scan_url_for_candidates, province, item["url"], int(args.request_timeout_sec), args.year
            ): item
            for item in fetch_targets
        }
        for future in as_completed(futures):
            meta = futures[future]
            try:
                found = future.result()
            except Exception:
                continue
            for candidate in found:
                candidate["search_score"] = meta.get("search_score", 0)
                candidate["search_title"] = str(meta.get("title", ""))[:120]
                candidate["search_query"] = meta.get("query", "")
                candidate["search_engine"] = meta.get("engine", "")
            candidates.extend(found)

    deduplicated = dedup(candidates)
    top_n = deduplicated[: max(1, int(args.max_candidates))]
    selected_urls = [item.get("url", "") for item in selected if item.get("url")]
    return {
        "finished": True,
        "searched_at": datetime.now().isoformat(timespec="seconds"),
        "engines": engines,
        "engine_mode": args.engine_mode,
        "per_domain_cap": int(args.per_domain_cap),
        "queries": query_debug,
        "anti_spider_hits": anti_count,
        "url_count_raw": len(url_rows),
        "url_count": len(selected),
        "fetch_count": len(fetch_targets),
        "selected_urls": selected_urls[:100],
        "selected_url_meta": [
            {
                "url": item.get("url", ""),
                "search_score": item.get("search_score", 0),
                "engine": item.get("engine", ""),
                "query": item.get("query", ""),
                "title": str(item.get("title", ""))[:120],
            }
            for item in selected[:60]
        ],
        "candidate_count": len(deduplicated),
        "top_candidates": top_n,
    }


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    args = parse_args()
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    engines = parse_engines(args.engines)
    domain_filters = parse_domain_filter(args.domain_filter)

    if args.provinces.strip():
        provinces = [item.strip() for item in args.provinces.split(",") if item.strip()]
    else:
        provinces = load_missing_provinces(args.year)
    if not provinces:
        logging.info("no provinces to process")
        return

    result: dict[str, dict[str, Any]] = load_existing_json(output_path) if args.resume else {}
    to_run: list[str] = []
    for province in provinces:
        if args.force:
            to_run.append(province)
            continue
        previous = result.get(province) if isinstance(result, dict) else None
        if previous and previous.get("finished"):
            logging.info("[SKIP] %s (resume hit)", province)
            continue
        to_run.append(province)

    if not to_run:
        logging.info("all target provinces are already completed in output file")
        return

    addon_paths: list[str] = []
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
    logging.info(
        "provinces=%s, engines=%s, engine_mode=%s, fetch_workers=%s, province_workers=%s, max_pages=%s, "
        "max_fetch_pages=%s, per_domain_cap=%s, domain_filter=%s",
        len(to_run),
        engines,
        args.engine_mode,
        args.fetch_workers,
        args.province_workers,
        args.max_pages,
        max_fetch_pages,
        args.per_domain_cap,
        domain_filters or "ALL",
    )

    def open_browser() -> Camoufox:
        return Camoufox(
            headless=headless_mode,
            os="windows",
            humanize=True,
            locale=["zh-CN", "zh"],
            addons=addon_paths,
            firefox_user_prefs=firefox_user_prefs,
        )

    result_lock = threading.Lock()

    def save_province_result(province_name: str, record: dict[str, Any]) -> None:
        with result_lock:
            result[province_name] = record
            save_json(output_path, result)

    def worker_loop(worker_id: int, province_list: list[str]) -> None:
        if not province_list:
            return
        worker_tag = f"W{worker_id}"
        browser_cm = open_browser()
        browser = browser_cm.__enter__()
        try:
            for province in province_list:
                logging.info("[RUN][%s] %s", worker_tag, province)
                retried = 0
                while True:
                    try:
                        record = process_single_province(
                            browser, province, args, engines, max_fetch_pages, domain_filters
                        )
                        record["worker"] = worker_tag
                        save_province_result(province, record)
                        logging.info(
                            "[OK][%s] urls_raw=%s selected=%s fetch=%s anti=%s candidates=%s",
                            worker_tag,
                            record.get("url_count_raw", 0),
                            record.get("url_count", 0),
                            record.get("fetch_count", 0),
                            record.get("anti_spider_hits", 0),
                            record.get("candidate_count", 0),
                        )
                        break
                    except Exception as exc:
                        message = str(exc)
                        recoverable = "Target page" in message or "browser has been closed" in message
                        if recoverable and retried < 2:
                            retried += 1
                            logging.warning("[WARN][%s] browser crashed, restart and retry (%s/2)", worker_tag, retried)
                            with contextlib.suppress(Exception):
                                browser_cm.__exit__(None, None, None)
                            browser_cm = open_browser()
                            browser = browser_cm.__enter__()
                            continue
                        save_province_result(
                            province,
                            {
                                "finished": False,
                                "searched_at": datetime.now().isoformat(timespec="seconds"),
                                "error": message[:300],
                                "worker": worker_tag,
                            },
                        )
                        logging.error("[ERR][%s] %s: %s", worker_tag, province, message)
                        break
        finally:
            with contextlib.suppress(Exception):
                browser_cm.__exit__(None, None, None)

    province_workers = max(1, min(int(args.province_workers), len(to_run)))
    if province_workers <= 1:
        worker_loop(1, to_run)
    else:
        buckets: list[list[str]] = [[] for _ in range(province_workers)]
        for index, province in enumerate(to_run):
            buckets[index % province_workers].append(province)
        with ThreadPoolExecutor(max_workers=province_workers) as executor:
            futures = [executor.submit(worker_loop, i + 1, buckets[i]) for i in range(province_workers) if buckets[i]]
            for future in as_completed(futures):
                future.result()

    save_json(output_path, result)
    logging.info("[DONE] saved: %s", output_path)


if __name__ == "__main__":
    main()
