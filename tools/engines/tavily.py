from __future__ import annotations

from typing import Any

import requests  # type: ignore[import-untyped]

from .base import SearchEngine, SearchResult


class TavilySearchEngine(SearchEngine):
    name = "tavily"

    def search(self, query: str, page: Any, **kwargs: Any) -> list[SearchResult]:
        _ = page
        api_key = str(kwargs.get("api_key") or "")
        if not api_key:
            self.last_meta = {"skipped": "missing_api_key"}
            return []

        endpoint = str(kwargs.get("endpoint") or "https://api.tavily.com/search")
        max_results = int(kwargs.get("max_results", 10))
        topic = str(kwargs.get("topic") or "general")
        payload = {
            "api_key": api_key,
            "query": query,
            "search_depth": "advanced",
            "max_results": max(1, min(max_results, 20)),
            "topic": topic,
            "include_answer": False,
            "include_images": False,
            "include_raw_content": False,
        }
        response = requests.post(endpoint, json=payload, timeout=25)
        if response.status_code != 200:
            self.last_meta = {"status_code": response.status_code}
            return []
        data = response.json()
        results = data.get("results", []) if isinstance(data, dict) else []
        out: list[SearchResult] = []
        for item in results:
            if not isinstance(item, dict):
                continue
            url = (item.get("url") or "").strip()
            title = (item.get("title") or "").strip()
            snippet = (item.get("content") or "").strip()
            if not url or not title:
                continue
            out.append(SearchResult(title=title, url=url, snippet=snippet))
        self.last_meta = {"result_count": len(out)}
        return out
