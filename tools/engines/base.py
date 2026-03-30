from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class SearchResult:
    title: str
    url: str
    snippet: str = ""


class SearchEngine(ABC):
    """Abstract search engine adapter."""

    name: str = ""

    def __init__(self) -> None:
        self.last_meta: dict[str, Any] = {}

    @abstractmethod
    def search(self, query: str, page: Any, **kwargs: Any) -> list[SearchResult]:
        """Search and return normalized results."""

    def get_last_meta(self) -> dict[str, Any]:
        return dict(self.last_meta)
