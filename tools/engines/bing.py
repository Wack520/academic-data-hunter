from __future__ import annotations

import random
from typing import Any

import requests  # type: ignore[import-untyped]

from .base import SearchEngine, SearchResult


class BingSearchEngine(SearchEngine):
    name = "bing"

    def search(self, query: str, page: Any, **kwargs: Any) -> list[SearchResult]:
        timeout = int(kwargs.get("timeout_ms", 45_000))
        url = "https://www.bing.com/search?q=" + requests.utils.quote(query)
        page.goto(url, timeout=timeout, wait_until="domcontentloaded")
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
        self.last_meta = {}
        out: list[SearchResult] = []
        for row in rows or []:
            title = (row.get("title") or "").strip()
            url = (row.get("data_url") or "").strip()
            if not url:
                continue
            out.append(SearchResult(title=title, url=url, snippet=(row.get("snippet") or "").strip()))
        return out
