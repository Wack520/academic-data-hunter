from __future__ import annotations

import asyncio
import functools
import logging
import re
import time
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

import requests  # type: ignore[import-untyped]
from bs4 import BeautifulSoup

from tools.config import (
    FETCH_CACHE_MAX_SIZE,
    FETCH_DEFAULT_RETRIES,
    FETCH_DEFAULT_TIMEOUT_SEC,
    FETCH_RETRY_SLEEP_SEC,
    FETCH_SSL_VERIFY,
    FETCH_USER_AGENT,
)

UA = {"User-Agent": FETCH_USER_AGENT}

_CACHE_MAX_SIZE = FETCH_CACHE_MAX_SIZE

_aiohttp_mod: Any
try:
    import aiohttp as _aiohttp_mod  # type: ignore[import-untyped]
except Exception:  # pragma: no cover - optional dependency
    _aiohttp_mod = None

aiohttp: Any = _aiohttp_mod

_HAS_AIOHTTP = aiohttp is not None
_FALLBACK_WARNED = False

if TYPE_CHECKING:  # pragma: no cover
    import aiohttp as aiohttp_types


def fetch_text(url: str, retries: int = FETCH_DEFAULT_RETRIES, timeout_sec: int = FETCH_DEFAULT_TIMEOUT_SEC) -> str:
    last_err: Exception | None = None
    for _ in range(retries + 1):
        try:
            response = requests.get(url, headers=UA, timeout=timeout_sec, verify=FETCH_SSL_VERIFY)
            if response.status_code != 200:
                raise RuntimeError(f"status={response.status_code}")
            response.encoding = response.apparent_encoding or "utf-8"
            text = BeautifulSoup(response.text, "html.parser").get_text(" ")
            return re.sub(r"\s+", " ", text)
        except Exception as exc:
            last_err = exc
            time.sleep(FETCH_RETRY_SLEEP_SEC)
    raise RuntimeError(f"fetch failed: {url}, err={last_err}")


@functools.lru_cache(maxsize=_CACHE_MAX_SIZE)
def _cached_fetch(
    url: str,
    retries: int = FETCH_DEFAULT_RETRIES,
    timeout_sec: int = FETCH_DEFAULT_TIMEOUT_SEC,
) -> str:
    """Cache only successful fetch results.

    Exceptions raised by ``fetch_text`` are not cached by ``lru_cache``, so
    temporary failures will be retried on subsequent calls.
    """
    return fetch_text(url, retries=retries, timeout_sec=timeout_sec)


def get_or_fetch_text(
    url: str,
    retries: int = FETCH_DEFAULT_RETRIES,
    timeout_sec: int = FETCH_DEFAULT_TIMEOUT_SEC,
) -> str:
    """Thread-safe cached fetch with bounded cache (successes only)."""
    return _cached_fetch(url, retries=retries, timeout_sec=timeout_sec)


async def _fetch_text_with_session(
    session: aiohttp_types.ClientSession,
    url: str,
    retries: int = FETCH_DEFAULT_RETRIES,
    timeout_sec: int = FETCH_DEFAULT_TIMEOUT_SEC,
) -> str:
    last_err: Exception | None = None
    for _ in range(retries + 1):
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    raise RuntimeError(f"status={response.status}")
                html = await response.text(errors="ignore")
                text = BeautifulSoup(html, "html.parser").get_text(" ")
                return re.sub(r"\s+", " ", text)
        except Exception as exc:
            last_err = exc
            await asyncio.sleep(FETCH_RETRY_SLEEP_SEC)
    raise RuntimeError(f"fetch failed: {url}, err={last_err}")


async def fetch_many_texts_async(
    urls: Iterable[str],
    *,
    max_concurrency: int = 12,
    retries: int = FETCH_DEFAULT_RETRIES,
    timeout_sec: int = FETCH_DEFAULT_TIMEOUT_SEC,
) -> dict[str, tuple[bool, str]]:
    """Batch fetch URL texts with async concurrency.

    Returns:
      {url: (ok, payload)}, where payload is text on success or error message on failure.
    """
    deduped_urls = [url for url in dict.fromkeys(urls) if isinstance(url, str) and url.strip()]
    if not deduped_urls:
        return {}

    limit = max(1, int(max_concurrency))
    semaphore = asyncio.Semaphore(limit)

    async def _worker_with_session(session: aiohttp_types.ClientSession, url: str) -> tuple[str, tuple[bool, str]]:
        async with semaphore:
            try:
                text = await _fetch_text_with_session(session, url, retries=retries, timeout_sec=timeout_sec)
                return url, (True, text)
            except Exception as exc:
                return url, (False, str(exc))

    async def _worker_without_aiohttp(url: str) -> tuple[str, tuple[bool, str]]:
        async with semaphore:
            try:
                text = await asyncio.to_thread(fetch_text, url, retries, timeout_sec)
                return url, (True, text)
            except Exception as exc:
                return url, (False, str(exc))

    if not _HAS_AIOHTTP:
        global _FALLBACK_WARNED
        if not _FALLBACK_WARNED:
            logging.warning("aiohttp not installed; async fetch falls back to asyncio.to_thread + requests")
            _FALLBACK_WARNED = True
        pairs = await asyncio.gather(*(_worker_without_aiohttp(url) for url in deduped_urls))
        return dict(pairs)

    timeout = aiohttp.ClientTimeout(total=timeout_sec)
    connector = aiohttp.TCPConnector(limit=limit, ssl=FETCH_SSL_VERIFY)
    async with aiohttp.ClientSession(headers=UA, timeout=timeout, connector=connector) as session:
        pairs = await asyncio.gather(*(_worker_with_session(session, url) for url in deduped_urls))
    return dict(pairs)
