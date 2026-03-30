from __future__ import annotations

import random
from typing import Any

import requests  # type: ignore[import-untyped]

from .base import SearchEngine, SearchResult


class So360SearchEngine(SearchEngine):
    name = "360"

    def search(self, query: str, page: Any, **kwargs: Any) -> list[SearchResult]:
        timeout = int(kwargs.get("timeout_ms", 45_000))
        url = "https://www.so.com/s?q=" + requests.utils.quote(query)
        page.goto(url, timeout=timeout, wait_until="domcontentloaded")
        page.wait_for_timeout(random.randint(900, 1500))
        anti = "qcaptcha.so.com" in page.url
        if anti:
            self.last_meta = {"anti_360": True}
            return []
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
        self.last_meta = {"anti_360": False}
        out: list[SearchResult] = []
        for row in rows or []:
            title = (row.get("title") or "").strip()
            item_url = (row.get("data_url") or "").strip()
            if not item_url:
                continue
            out.append(SearchResult(title=title, url=item_url, snippet=(row.get("snippet") or "").strip()))
        return out
