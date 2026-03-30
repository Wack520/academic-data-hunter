from __future__ import annotations

import functools
import re
import time

import requests  # type: ignore[import-untyped]
from bs4 import BeautifulSoup

UA = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

_CACHE_MAX_SIZE = 512


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


@functools.lru_cache(maxsize=_CACHE_MAX_SIZE)
def _cached_fetch(url: str, retries: int = 2, timeout_sec: int = 18) -> tuple[bool, str]:
    try:
        return True, fetch_text(url, retries=retries, timeout_sec=timeout_sec)
    except Exception as exc:
        return False, str(exc)


def get_or_fetch_text(url: str, retries: int = 2, timeout_sec: int = 18) -> str:
    """Thread-safe cached fetch with bounded cache and cached failure details."""
    ok, payload = _cached_fetch(url, retries=retries, timeout_sec=timeout_sec)
    if ok:
        return payload
    raise RuntimeError(payload)
