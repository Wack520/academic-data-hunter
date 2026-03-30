from __future__ import annotations

from .base import SearchEngine
from .bing import BingSearchEngine
from .google import GoogleSearchEngine
from .so360 import So360SearchEngine
from .sogou import SogouSearchEngine
from .tavily import TavilySearchEngine

_ENGINE_REGISTRY: dict[str, type[SearchEngine]] = {
    "sogou": SogouSearchEngine,
    "360": So360SearchEngine,
    "bing": BingSearchEngine,
    "google": GoogleSearchEngine,
    "tavily": TavilySearchEngine,
}


def get_engine(name: str) -> SearchEngine:
    key = (name or "").strip().lower()
    if key not in _ENGINE_REGISTRY:
        supported = ", ".join(sorted(_ENGINE_REGISTRY.keys()))
        raise ValueError(f"unsupported engine: {name}, supported={supported}")
    return _ENGINE_REGISTRY[key]()


def supported_engines() -> tuple[str, ...]:
    return tuple(_ENGINE_REGISTRY.keys())
