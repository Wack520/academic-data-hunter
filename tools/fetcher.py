from __future__ import annotations

import re
import threading
import time

import requests  # type: ignore[import-untyped]
from bs4 import BeautifulSoup

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

PAGE_TEXT_CACHE: dict[str, str] = {}
PAGE_ERR_CACHE: dict[str, str] = {}
PAGE_CACHE_LOCK = threading.Lock()


def fetch_text(url: str, retries: int = 2, timeout_sec: int = 18) -> str:
    last_err: Exception | None = None
    for _ in range(retries + 1):
        try:
            response = requests.get(url, headers=UA, timeout=timeout_sec)
            if response.status_code != 200:
                raise RuntimeError(f"status={response.status_code}")
            response.encoding = response.apparent_encoding or "utf-8"
            text = BeautifulSoup(response.text, "html.parser").get_text(" ")
            return re.sub(r"\s+", " ", text)
        except Exception as exc:
            last_err = exc
            time.sleep(0.4)
    raise RuntimeError(f"fetch failed: {url}, err={last_err}")


def get_or_fetch_text(url: str, retries: int = 2, timeout_sec: int = 18) -> str:
    with PAGE_CACHE_LOCK:
        if url in PAGE_TEXT_CACHE:
            return PAGE_TEXT_CACHE[url]
        if url in PAGE_ERR_CACHE:
            raise RuntimeError(PAGE_ERR_CACHE[url])

    try:
        text = fetch_text(url, retries=retries, timeout_sec=timeout_sec)
    except Exception as exc:
        with PAGE_CACHE_LOCK:
            PAGE_ERR_CACHE[url] = str(exc)
        raise

    with PAGE_CACHE_LOCK:
        PAGE_TEXT_CACHE[url] = text
    return text
