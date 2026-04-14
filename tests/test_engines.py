"""Tests for tools.engines — registry, base classes, and individual engine adapters."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tools.engines import SearchEngine, SearchResult, get_engine, supported_engines
from tools.engines.base import SearchEngine as BaseSearchEngine
from tools.engines.bing import BingSearchEngine
from tools.engines.google import GoogleSearchEngine, _to_result_rows
from tools.engines.so360 import So360SearchEngine
from tools.engines.sogou import SogouSearchEngine
from tools.engines.tavily import TavilySearchEngine

# ─── SearchResult dataclass ─────────────────────────────────


class TestSearchResult:
    def test_create_minimal(self):
        r = SearchResult(title="Hello", url="https://example.com")
        assert r.title == "Hello"
        assert r.url == "https://example.com"
        assert r.snippet == ""

    def test_create_full(self):
        r = SearchResult(title="T", url="https://a.cn", snippet="S")
        assert r.snippet == "S"


# ─── Registry ───────────────────────────────────────────────


class TestRegistry:
    def test_supported_engines_not_empty(self):
        names = supported_engines()
        assert isinstance(names, tuple)
        assert len(names) >= 5
        for exp in ("google", "bing", "sogou", "360", "tavily"):
            assert exp in names

    def test_get_engine_returns_correct_type(self):
        eng = get_engine("google")
        assert isinstance(eng, GoogleSearchEngine)
        assert isinstance(eng, SearchEngine)

    def test_get_engine_case_insensitive(self):
        eng = get_engine("  BING  ")
        assert isinstance(eng, BingSearchEngine)

    def test_get_engine_unknown_raises(self):
        with pytest.raises(ValueError, match="unsupported engine"):
            get_engine("nonexistent_engine")

    def test_all_registered_engines_instantiate(self):
        for name in supported_engines():
            eng = get_engine(name)
            assert eng.last_meta == {}
            assert hasattr(eng, "search")


# ─── Base class ──────────────────────────────────────────────


class TestBaseEngine:
    def test_abstract_cannot_instantiate(self):
        with pytest.raises(TypeError):
            BaseSearchEngine()  # type: ignore[abstract]

    def test_get_last_meta_returns_copy(self):
        eng = get_engine("google")
        eng.last_meta = {"key": "value"}
        meta = eng.get_last_meta()
        assert meta == {"key": "value"}
        meta["key"] = "changed"
        assert eng.last_meta["key"] == "value"  # original not mutated


# ─── Google Engine ───────────────────────────────────────────


class TestGoogleEngine:
    def test_to_result_rows_none(self):
        assert _to_result_rows(None) == []

    def test_to_result_rows_empty(self):
        assert _to_result_rows([]) == []

    def test_to_result_rows_filters_empty_url(self):
        rows = [
            {"title": "A", "data_url": "https://a.com", "snippet": "s1"},
            {"title": "B", "data_url": "", "snippet": "s2"},
            {"title": "C", "data_url": "https://c.com"},
        ]
        results = _to_result_rows(rows)
        assert len(results) == 2
        assert results[0].title == "A"
        assert results[1].url == "https://c.com"
        assert results[1].snippet == ""

    def test_search_with_mock_page(self):
        page = MagicMock()
        page.url = "https://www.google.com/search?q=test"
        page.evaluate.return_value = [
            {"title": "Result 1", "data_url": "https://example.com/1", "snippet": "snip 1"},
        ]

        eng = GoogleSearchEngine()
        results = eng.search("test query", page)
        assert len(results) == 1
        assert results[0].title == "Result 1"
        page.goto.assert_called_once()
        page.wait_for_timeout.assert_called_once()
        assert eng.last_meta["anti_google"] is False

    def test_search_detects_anti_redirect(self):
        page = MagicMock()
        page.url = "https://www.google.com/sorry/index"
        page.evaluate.return_value = []

        eng = GoogleSearchEngine()
        results = eng.search("test", page)
        assert results == []
        assert eng.last_meta["anti_google"] is True


# ─── Bing Engine ─────────────────────────────────────────────


class TestBingEngine:
    def test_search_with_mock_page(self):
        page = MagicMock()
        page.evaluate.return_value = [
            {"title": "Bing Result", "data_url": "https://bing.com/r", "snippet": "s"},
        ]

        eng = BingSearchEngine()
        results = eng.search("query", page, timeout_ms=30_000)
        assert len(results) == 1
        assert results[0].title == "Bing Result"

    def test_search_empty_results(self):
        page = MagicMock()
        page.evaluate.return_value = None

        eng = BingSearchEngine()
        results = eng.search("query", page)
        assert results == []


# ─── Sogou Engine ────────────────────────────────────────────


class TestSogouEngine:
    def test_search_with_mock_page(self):
        page = MagicMock()
        page.url = "https://www.sogou.com/web?query=test"
        page.evaluate.return_value = [
            {"title": "Sogou Result", "data_url": "https://sogou.com/r", "snippet": "s"},
        ]

        eng = SogouSearchEngine()
        results = eng.search("test", page)
        assert len(results) == 1
        assert eng.last_meta["anti_sogou"] is False

    def test_antispider_detected(self):
        page = MagicMock()
        page.url = "https://www.sogou.com/antispider/?key=abc"
        page.evaluate.return_value = []

        eng = SogouSearchEngine()
        eng.search("test", page)
        assert eng.last_meta["anti_sogou"] is True


# ─── So360 Engine ────────────────────────────────────────────


class TestSo360Engine:
    def test_search_with_mock_page(self):
        page = MagicMock()
        page.evaluate.return_value = [
            {"title": "360 Result", "data_url": "https://360.cn/r", "snippet": "s"},
        ]

        eng = So360SearchEngine()
        results = eng.search("test", page)
        assert len(results) == 1
        assert results[0].url == "https://360.cn/r"


# ─── Tavily Engine ───────────────────────────────────────────


class TestTavilyEngine:
    def test_search_skips_without_api_key(self):
        eng = TavilySearchEngine()
        results = eng.search("test", page=None)
        assert results == []
        assert eng.last_meta.get("skipped") == "missing_api_key"

    @patch("tools.engines.tavily.requests.post")
    def test_search_success(self, mock_post: MagicMock):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "results": [
                {"url": "https://a.com", "title": "A", "content": "snippet A"},
                {"url": "", "title": "B", "content": "no url"},
                {"url": "https://c.com", "title": "", "content": "no title"},
            ]
        }
        mock_post.return_value = mock_resp

        eng = TavilySearchEngine()
        results = eng.search("test", page=None, api_key="fake_key")
        assert len(results) == 1
        assert results[0].title == "A"
        assert results[0].snippet == "snippet A"
        assert eng.last_meta["result_count"] == 1

    @patch("tools.engines.tavily.requests.post")
    def test_search_non_200(self, mock_post: MagicMock):
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_post.return_value = mock_resp

        eng = TavilySearchEngine()
        results = eng.search("test", page=None, api_key="key")
        assert results == []
        assert eng.last_meta["status_code"] == 429

    @patch("tools.engines.tavily.requests.post")
    def test_search_non_dict_response(self, mock_post: MagicMock):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = "unexpected string"
        mock_post.return_value = mock_resp

        eng = TavilySearchEngine()
        results = eng.search("test", page=None, api_key="key")
        assert results == []
