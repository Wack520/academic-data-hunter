from __future__ import annotations

import asyncio
from types import SimpleNamespace

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

    def fake_get(url: str, headers: dict[str, str], timeout: int, verify: bool) -> FakeResponse:
        _ = (url, headers, timeout)
        assert verify == fetcher.FETCH_SSL_VERIFY
        calls["count"] += 1
        return FakeResponse()

    monkeypatch.setattr(fetcher.requests, "get", fake_get)

    url = "https://example.com/a"
    text1 = fetcher.get_or_fetch_text(url, retries=0, timeout_sec=5)
    text2 = fetcher.get_or_fetch_text(url, retries=0, timeout_sec=5)

    assert calls["count"] == 1
    assert text1 == text2
    assert "hello world" in text1


def test_get_or_fetch_text_does_not_cache_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"count": 0}

    def fake_get(url: str, headers: dict[str, str], timeout: int, verify: bool) -> None:
        _ = (url, headers, timeout, verify)
        calls["count"] += 1
        raise RuntimeError("network down")

    monkeypatch.setattr(fetcher.requests, "get", fake_get)

    url = "https://example.com/b"
    with pytest.raises(RuntimeError):
        fetcher.get_or_fetch_text(url, retries=0, timeout_sec=5)
    with pytest.raises(RuntimeError):
        fetcher.get_or_fetch_text(url, retries=0, timeout_sec=5)

    assert calls["count"] == 2


def test_fetch_many_texts_async_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"count": 0}

    def fake_fetch_text(url: str, retries: int = 0, timeout_sec: int = 5) -> str:
        _ = (retries, timeout_sec)
        calls["count"] += 1
        if "bad" in url:
            raise RuntimeError("boom")
        return f"text:{url}"

    monkeypatch.setattr(fetcher, "_HAS_AIOHTTP", False)
    monkeypatch.setattr(fetcher, "fetch_text", fake_fetch_text)

    result = asyncio.run(
        fetcher.fetch_many_texts_async(
            ["https://example.com/good", "https://example.com/bad"],
            max_concurrency=2,
            retries=0,
            timeout_sec=5,
        )
    )

    assert calls["count"] == 2
    assert result["https://example.com/good"] == (True, "text:https://example.com/good")
    assert result["https://example.com/bad"][0] is False


def test_fetch_many_texts_async_fallback_warns_only_once(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr(fetcher, "_HAS_AIOHTTP", False)
    monkeypatch.setattr(fetcher, "_FALLBACK_WARNED", False)
    monkeypatch.setattr(fetcher, "fetch_text", lambda url, retries=0, timeout_sec=5: f"text:{url}")

    caplog.set_level("WARNING")
    asyncio.run(fetcher.fetch_many_texts_async(["https://example.com/a"]))
    asyncio.run(fetcher.fetch_many_texts_async(["https://example.com/b"]))

    warning_records = [rec for rec in caplog.records if rec.levelname == "WARNING"]
    assert len(warning_records) == 1


def test_fetch_text_retries_non_200_then_success(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = {"count": 0}

    class FakeResponse:
        def __init__(self, status_code: int, text: str):
            self.status_code = status_code
            self.apparent_encoding = "utf-8"
            self.text = text
            self.encoding = None

    def fake_get(url: str, headers: dict[str, str], timeout: int, verify: bool) -> FakeResponse:
        _ = (url, headers, timeout, verify)
        calls["count"] += 1
        if calls["count"] == 1:
            return FakeResponse(503, "<html><body>bad</body></html>")
        return FakeResponse(200, "<html><body>ok  value</body></html>")

    monkeypatch.setattr(fetcher.requests, "get", fake_get)
    monkeypatch.setattr(fetcher.time, "sleep", lambda _: None)

    text = fetcher.fetch_text("https://example.com/retry", retries=1, timeout_sec=5)
    assert calls["count"] == 2
    assert "ok value" in text


class _FakeAsyncResponse:
    def __init__(self, status: int, html: str):
        self.status = status
        self._html = html

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        _ = (exc_type, exc, tb)
        return False

    async def text(self, errors: str = "ignore") -> str:
        _ = errors
        return self._html


def test_fetch_text_with_session_retries_and_success(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeSession:
        def __init__(self) -> None:
            self.calls = 0

        def get(self, url: str) -> _FakeAsyncResponse:
            _ = url
            self.calls += 1
            if self.calls == 1:
                return _FakeAsyncResponse(500, "<html>bad</html>")
            return _FakeAsyncResponse(200, "<html><body>done  text</body></html>")

    async def fake_sleep(_: float) -> None:
        return None

    session = FakeSession()
    monkeypatch.setattr(fetcher.asyncio, "sleep", fake_sleep)
    text = asyncio.run(fetcher._fetch_text_with_session(session, "https://example.com/x", retries=1, timeout_sec=3))
    assert session.calls == 2
    assert "done text" in text


def test_fetch_text_with_session_raises_after_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeSession:
        def get(self, url: str) -> _FakeAsyncResponse:
            _ = url
            return _FakeAsyncResponse(502, "<html>bad</html>")

    async def fake_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(fetcher.asyncio, "sleep", fake_sleep)
    with pytest.raises(RuntimeError, match="fetch failed"):
        asyncio.run(
            fetcher._fetch_text_with_session(FakeSession(), "https://example.com/fail", retries=1, timeout_sec=3)
        )


def test_fetch_many_texts_async_with_fake_aiohttp(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeTimeout:
        def __init__(self, total: int):
            self.total = total

    class FakeConnector:
        def __init__(self, limit: int, ssl: bool):
            self.limit = limit
            self.ssl = ssl

    class FakeClientSession:
        def __init__(self, headers: dict[str, str], timeout: FakeTimeout, connector: FakeConnector):
            captured["headers"] = headers
            captured["timeout"] = timeout
            captured["connector"] = connector
            self.attempts: dict[str, int] = {}

        async def __aenter__(self) -> FakeClientSession:
            return self

        async def __aexit__(self, exc_type, exc, tb) -> bool:
            _ = (exc_type, exc, tb)
            return False

        def get(self, url: str) -> _FakeAsyncResponse:
            self.attempts[url] = self.attempts.get(url, 0) + 1
            if "fail" in url:
                raise RuntimeError("network")
            if "retry" in url and self.attempts[url] == 1:
                return _FakeAsyncResponse(500, "<html>bad</html>")
            return _FakeAsyncResponse(200, f"<html><body>{url}</body></html>")

    fake_aiohttp = SimpleNamespace(
        ClientTimeout=FakeTimeout,
        TCPConnector=FakeConnector,
        ClientSession=FakeClientSession,
    )

    async def fake_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(fetcher, "_HAS_AIOHTTP", True)
    monkeypatch.setattr(fetcher, "aiohttp", fake_aiohttp)
    monkeypatch.setattr(fetcher.asyncio, "sleep", fake_sleep)

    raw_urls = [
        "https://example.com/retry",
        "https://example.com/retry",
        "https://example.com/fail",
        "https://example.com/ok",
        "",
    ]
    result = asyncio.run(fetcher.fetch_many_texts_async(raw_urls, max_concurrency=2, retries=1, timeout_sec=3))

    assert set(result.keys()) == {
        "https://example.com/retry",
        "https://example.com/fail",
        "https://example.com/ok",
    }
    assert result["https://example.com/retry"][0] is True
    assert result["https://example.com/ok"][0] is True
    assert result["https://example.com/fail"][0] is False
    assert isinstance(captured["timeout"], FakeTimeout)
    assert isinstance(captured["connector"], FakeConnector)
    assert captured["timeout"].total == 3
    assert captured["connector"].limit == 2
    assert captured["connector"].ssl == fetcher.FETCH_SSL_VERIFY


def test_fetch_many_texts_async_empty_urls_returns_empty_dict() -> None:
    result = asyncio.run(fetcher.fetch_many_texts_async([], max_concurrency=2, retries=0, timeout_sec=3))
    assert result == {}
