from __future__ import annotations

import random
from typing import Any

import requests  # type: ignore[import-untyped]

from .base import SearchEngine, SearchResult


class SogouSearchEngine(SearchEngine):
    name = "sogou"

    def search(self, query: str, page: Any, **kwargs: Any) -> list[SearchResult]:
        timeout = int(kwargs.get("timeout_ms", 45_000))
        url = "https://www.sogou.com/web?query=" + requests.utils.quote(query)
        page.goto(url, timeout=timeout, wait_until="domcontentloaded")
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
        self.last_meta = {"anti_sogou": anti}
        out: list[SearchResult] = []
        for row in rows or []:
            title = (row.get("title") or "").strip()
            url = (row.get("data_url") or "").strip()
            if not url:
                continue
            out.append(SearchResult(title=title, url=url, snippet=(row.get("snippet") or "").strip()))
        return out
