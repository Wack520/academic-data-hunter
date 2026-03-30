#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用网页数据处理管线（借鉴 ScrapeGraphAI 的“处理分层”思路）：
1) markdown-like 内容归档（低成本、可审计）
2) schema 规则抽取（结构化字段 + evidence）

输入可来自：
- discover_case02_nev_camoufox.py 的候选 JSON
- 自定义 URL 列表文件
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}


@dataclass
class FieldRule:
    name: str
    patterns: List[str]
    cast: str = "str"  # str|float|int
    unit: str = ""


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="网页数据处理（markdown归档 + schema抽取）")
    p.add_argument("--input-json", default="", help="discover 输出 JSON（可选）")
    p.add_argument("--urls-file", default="", help="纯文本URL列表（每行一个，可选）")
    p.add_argument("--schema-file", default="", help="抽取 schema JSON（可选）")
    p.add_argument("--output-dir", default="tmp/processed", help="输出目录")
    p.add_argument("--mode", choices=["markdown", "extract", "both"], default="both")
    p.add_argument("--max-urls", type=int, default=80)
    p.add_argument("--timeout-sec", type=int, default=18)
    p.add_argument("--retry", type=int, default=1)
    p.add_argument("--append", action="store_true", help="追加写入输出文件（默认覆盖）")
    return p.parse_args()


def load_urls_from_discover(path: Path) -> List[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    urls = []
    if not isinstance(data, dict):
        return urls
    for _, rec in data.items():
        if not isinstance(rec, dict):
            continue
        for u in rec.get("selected_urls", []) or []:
            u = (u or "").strip()
            if u.startswith("http://") or u.startswith("https://"):
                urls.append(u)
        tops = rec.get("top_candidates", [])
        for c in tops:
            if not isinstance(c, dict):
                continue
            u = (c.get("url") or "").strip()
            if u.startswith("http://") or u.startswith("https://"):
                urls.append(u)
    return urls


def load_urls_from_file(path: Path) -> List[str]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        u = line.strip()
        if not u or u.startswith("#"):
            continue
        if u.startswith("http://") or u.startswith("https://"):
            out.append(u)
    return out


def dedup_keep_order(arr: List[str]) -> List[str]:
    seen = set()
    out = []
    for x in arr:
        if x in seen:
            continue
        seen.add(x)
        out.append(x)
    return out


def fetch_html(url: str, timeout_sec: int, retry: int) -> str:
    last = None
    for i in range(retry + 1):
        try:
            r = requests.get(url, headers=UA, timeout=timeout_sec)
            r.raise_for_status()
            r.encoding = r.apparent_encoding or "utf-8"
            return r.text
        except Exception as e:  # noqa: BLE001
            last = e
            if i < retry:
                time.sleep(0.5 * (i + 1))
    raise RuntimeError(f"fetch failed: {last}")


def html_to_markdown_like(html: str) -> Dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    title = (soup.title.string if soup.title and soup.title.string else "").strip()

    headers = []
    for h in soup.find_all(["h1", "h2", "h3"]):
        t = re.sub(r"\s+", " ", h.get_text(" ", strip=True))
        if t:
            headers.append(t)
    headers = headers[:40]

    paras = []
    for p in soup.find_all(["p", "li"]):
        t = re.sub(r"\s+", " ", p.get_text(" ", strip=True))
        if t and len(t) >= 8:
            paras.append(t)
    paras = paras[:300]

    lines = []
    if title:
        lines.append(f"# {title}")
    for h in headers[:20]:
        lines.append(f"## {h}")
    for t in paras:
        lines.append(t)
    markdown_like = "\n\n".join(lines).strip()

    plain = re.sub(r"\s+", " ", soup.get_text(" ", strip=True)).strip()
    links = [a.get("href", "").strip() for a in soup.find_all("a", href=True)]
    links = [x for x in links if x]

    return {
        "title": title,
        "markdown_like": markdown_like,
        "plain_text": plain,
        "headers": headers,
        "links": links,
    }


def load_schema(path: Path) -> List[FieldRule]:
    data = json.loads(path.read_text(encoding="utf-8"))
    arr = data.get("fields", []) if isinstance(data, dict) else []
    out: List[FieldRule] = []
    for it in arr:
        if not isinstance(it, dict):
            continue
        name = (it.get("name") or "").strip()
        patterns = it.get("patterns") or []
        if not name or not isinstance(patterns, list) or not patterns:
            continue
        out.append(
            FieldRule(
                name=name,
                patterns=[str(x) for x in patterns if str(x).strip()],
                cast=str(it.get("cast") or "str"),
                unit=str(it.get("unit") or ""),
            )
        )
    return out


def cast_value(raw: str, cast: str):
    if cast == "float":
        return float(raw)
    if cast == "int":
        return int(float(raw))
    return raw


def extract_by_schema(text: str, rules: List[FieldRule]) -> Dict[str, Dict]:
    out = {}
    for rule in rules:
        got = None
        for p in rule.patterns:
            m = re.search(p, text)
            if not m:
                continue
            raw = m.group(1) if m.groups() else m.group(0)
            try:
                val = cast_value(raw, rule.cast)
            except Exception:
                val = raw
            got = {
                "value": val,
                "raw": raw,
                "unit": rule.unit,
                "evidence": re.sub(r"\s+", " ", m.group(0)).strip()[:220],
                "pattern": p,
            }
            break
        if got:
            out[rule.name] = got
    return out


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    urls: List[str] = []
    if args.input_json:
        p = Path(args.input_json)
        if p.exists():
            urls.extend(load_urls_from_discover(p))
    if args.urls_file:
        p = Path(args.urls_file)
        if p.exists():
            urls.extend(load_urls_from_file(p))

    urls = dedup_keep_order(urls)[: max(1, int(args.max_urls))]
    if not urls:
        logging.info("no urls")
        return

    rules: List[FieldRule] = []
    if args.schema_file:
        sp = Path(args.schema_file)
        if sp.exists():
            rules = load_schema(sp)

    md_jsonl = out_dir / "pages_markdown.jsonl"
    extract_jsonl = out_dir / "pages_extracted.jsonl"
    summary_csv = out_dir / "pages_summary.csv"

    if not args.append:
        for p in [md_jsonl, extract_jsonl, summary_csv]:
            if p.exists():
                p.unlink()

    rows = []
    ok = 0
    for u in urls:
        rec = {
            "url": u,
            "host": urlparse(u).netloc,
            "status": "ok",
            "title": "",
            "word_count": 0,
            "headers_count": 0,
            "links_count": 0,
            "error": "",
        }
        try:
            html = fetch_html(u, timeout_sec=int(args.timeout_sec), retry=int(args.retry))
            parsed = html_to_markdown_like(html)
            rec["title"] = parsed["title"]
            rec["word_count"] = len((parsed["plain_text"] or "").split())
            rec["headers_count"] = len(parsed["headers"])
            rec["links_count"] = len(parsed["links"])

            if args.mode in {"markdown", "both"}:
                with md_jsonl.open("a", encoding="utf-8") as f:
                    f.write(
                        json.dumps(
                            {
                                "url": u,
                                "title": parsed["title"],
                                "markdown_like": parsed["markdown_like"],
                                "headers": parsed["headers"][:40],
                                "links": parsed["links"][:120],
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )

            if args.mode in {"extract", "both"} and rules:
                extracted = extract_by_schema(parsed["plain_text"], rules)
                with extract_jsonl.open("a", encoding="utf-8") as f:
                    f.write(
                        json.dumps(
                            {
                                "url": u,
                                "title": parsed["title"],
                                "extracted": extracted,
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
            ok += 1
        except Exception as e:  # noqa: BLE001
            rec["status"] = "error"
            rec["error"] = str(e)[:220]
        rows.append(rec)

    with summary_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["url", "host", "status", "title", "word_count", "headers_count", "links_count", "error"],
        )
        w.writeheader()
        w.writerows(rows)

    logging.info("urls=%s ok=%s summary=%s", len(urls), ok, summary_csv)
    if args.mode in {"markdown", "both"}:
        logging.info("markdown=%s", md_jsonl)
    if args.mode in {"extract", "both"} and rules:
        logging.info("extracted=%s", extract_jsonl)


if __name__ == "__main__":
    main()
