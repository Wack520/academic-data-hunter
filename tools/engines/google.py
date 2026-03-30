from __future__ import annotations

import random
from typing import Any

import requests  # type: ignore[import-untyped]

from .base import SearchEngine, SearchResult


def _to_result_rows(rows: list[dict[str, Any]] | None) -> list[SearchResult]:
    out: list[SearchResult] = []
    for row in rows or []:
        title = (row.get("title") or "").strip()
        url = (row.get("data_url") or "").strip()
        if not url:
            continue
        out.append(SearchResult(title=title, url=url, snippet=(row.get("snippet") or "").strip()))
    return out


class GoogleSearchEngine(SearchEngine):
    name = "google"

    def search(self, query: str, page: Any, **kwargs: Any) -> list[SearchResult]:
        max_results = int(kwargs.get("max_results", 15))
        hl = str(kwargs.get("hl", "zh-CN"))
        gl = str(kwargs.get("gl", ""))
        timeout = int(kwargs.get("timeout_ms", 45_000))
        q = requests.utils.quote(query)
        url = f"https://www.google.com/search?q={q}&num={max(1, min(max_results, 50))}&hl={hl}"
        if gl:
            url += f"&gl={gl}"
        page.goto(url, timeout=timeout, wait_until="domcontentloaded")
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
        self.last_meta = {"anti_google": anti}
        return _to_result_rows(rows)
