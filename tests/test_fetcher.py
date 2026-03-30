from __future__ import annotations

import pytest

from tools import fetcher


@pytest.fixture(autouse=True)
def clear_fetch_cache() -> None:
    fetcher._cached_fetch.cache_clear()


def test_get_or_fetch_text_caches_success(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"count": 0}

    class FakeResponse:
        status_code = 200
        apparent_encoding = "utf-8"
        text = "<html><body> hello   world </body></html>"

    def fake_get(url: str, headers: dict[str, str], timeout: int) -> FakeResponse:
        _ = (url, headers, timeout)
        calls["count"] += 1
        return FakeResponse()

    monkeypatch.setattr(fetcher.requests, "get", fake_get)

    url = "https://example.com/a"
    text1 = fetcher.get_or_fetch_text(url, retries=0, timeout_sec=5)
    text2 = fetcher.get_or_fetch_text(url, retries=0, timeout_sec=5)

    assert calls["count"] == 1
    assert text1 == text2
    assert "hello world" in text1


def test_get_or_fetch_text_caches_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"count": 0}

    def fake_get(url: str, headers: dict[str, str], timeout: int) -> None:
        _ = (url, headers, timeout)
        calls["count"] += 1
        raise RuntimeError("network down")

    monkeypatch.setattr(fetcher.requests, "get", fake_get)

    url = "https://example.com/b"
    with pytest.raises(RuntimeError):
        fetcher.get_or_fetch_text(url, retries=0, timeout_sec=5)
    with pytest.raises(RuntimeError):
        fetcher.get_or_fetch_text(url, retries=0, timeout_sec=5)

    assert calls["count"] == 1
