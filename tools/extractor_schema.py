from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ExtractorSchema:
    required_term: str
    any_terms: tuple[str, ...]
    exclude_phrases: tuple[str, ...]
    value_tokens: tuple[str, ...]
    primary_pattern: str
    fallback_pattern: str
    unit_to_10k: dict[str, float]
    year_end_markers: tuple[str, ...]
    partial_year_markers: tuple[str, ...]
    province_scope_markers: tuple[str, ...]
    city_scope_markers: tuple[str, ...]
    national_scope_markers: tuple[str, ...]
    score_weights: dict[str, int]
    search_positive_terms: dict[str, int]
    search_negative_terms: dict[str, int]

    def resolve_year_end_markers(self, year: int) -> tuple[str, ...]:
        return tuple(marker.replace("{year}", str(year)) for marker in self.year_end_markers)


DEFAULT_EXTRACTOR_SCHEMA = ExtractorSchema(
    required_term="保有量",
    any_terms=("新能源", "电动汽车"),
    exclude_phrases=("全国新能源汽车保有量",),
    value_tokens=("新能源汽车保有量", "新能源车保有量", "电动汽车保有量"),
    primary_pattern=r"(?:达到|达|为|约为|突破)?\s*([0-9]+(?:\.[0-9]+)?)\s*({units})",
    fallback_pattern=(
        r"(?:新能源汽车|新能源车|电动汽车)[^。；，,]{0,40}(?:保有量)?[^0-9]{0,12}"
        r"([0-9]+(?:\.[0-9]+)?)\s*({units})"
    ),
    unit_to_10k={"万辆": 1.0, "辆": 0.0001},
    year_end_markers=(
        "截至{year}年底",
        "{year}年底",
        "{year}年末",
        "截至去年底",
        "截至去年末",
    ),
    partial_year_markers=("截至11月底", "截至10月底", "截至9月底", "截至今年9月30日"),
    province_scope_markers=("全省", "全区", "我省", "我区"),
    city_scope_markers=("全市",),
    national_scope_markers=("全国",),
    score_weights={
        "year_end": 8,
        "partial_year": 5,
        "province_scope": 4,
        "explicit_province": 4,
        "city_scope": -5,
        "national_scope": -9,
        "other_province": -8,
        "url_hint": 2,
        "search_province": 4,
        "search_year": 3,
    },
    search_positive_terms={
        "保有量": 4,
        "新能源": 3,
        "统计公报": 3,
        "政府": 3,
        "公安": 3,
        "国民经济和社会发展": 2,
    },
    search_negative_terms={
        "全国": -4,
        "全市": -3,
        "某市": -3,
    },
)


def _get_tuple_of_str(data: dict[str, Any], key: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw = data.get(key)
    if raw is None:
        return default
    if not isinstance(raw, list):
        raise ValueError(f"{key} must be list[str]")
    return tuple(str(item) for item in raw if str(item).strip())


def _get_str(data: dict[str, Any], key: str, default: str) -> str:
    raw = data.get(key)
    if raw is None:
        return default
    if not isinstance(raw, str):
        raise ValueError(f"{key} must be str")
    return raw


def _get_number_dict(
    data: dict[str, Any],
    key: str,
    default: Mapping[str, float | int],
    as_int: bool = False,
) -> dict[str, float]:
    raw = data.get(key)
    if raw is None:
        return dict(default)
    if not isinstance(raw, dict):
        raise ValueError(f"{key} must be object")

    out: dict[str, float] = {}
    for k, v in raw.items():
        if not isinstance(k, str):
            raise ValueError(f"{key} keys must be str")
        if not isinstance(v, (int, float)):
            raise ValueError(f"{key}.{k} must be number")
        out[k] = int(v) if as_int else float(v)
    return out


def load_extractor_schema(path: str | Path | None) -> ExtractorSchema:
    if not path:
        return DEFAULT_EXTRACTOR_SCHEMA

    schema_path = Path(path)
    if not schema_path.exists():
        raise FileNotFoundError(f"schema file not found: {schema_path}")

    data = json.loads(schema_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("extractor schema root must be object")

    merged = ExtractorSchema(
        required_term=_get_str(data, "required_term", DEFAULT_EXTRACTOR_SCHEMA.required_term),
        any_terms=_get_tuple_of_str(data, "any_terms", DEFAULT_EXTRACTOR_SCHEMA.any_terms),
        exclude_phrases=_get_tuple_of_str(data, "exclude_phrases", DEFAULT_EXTRACTOR_SCHEMA.exclude_phrases),
        value_tokens=_get_tuple_of_str(data, "value_tokens", DEFAULT_EXTRACTOR_SCHEMA.value_tokens),
        primary_pattern=_get_str(data, "primary_pattern", DEFAULT_EXTRACTOR_SCHEMA.primary_pattern),
        fallback_pattern=_get_str(data, "fallback_pattern", DEFAULT_EXTRACTOR_SCHEMA.fallback_pattern),
        unit_to_10k=_get_number_dict(data, "unit_to_10k", DEFAULT_EXTRACTOR_SCHEMA.unit_to_10k),
        year_end_markers=_get_tuple_of_str(data, "year_end_markers", DEFAULT_EXTRACTOR_SCHEMA.year_end_markers),
        partial_year_markers=_get_tuple_of_str(
            data,
            "partial_year_markers",
            DEFAULT_EXTRACTOR_SCHEMA.partial_year_markers,
        ),
        province_scope_markers=_get_tuple_of_str(
            data,
            "province_scope_markers",
            DEFAULT_EXTRACTOR_SCHEMA.province_scope_markers,
        ),
        city_scope_markers=_get_tuple_of_str(
            data,
            "city_scope_markers",
            DEFAULT_EXTRACTOR_SCHEMA.city_scope_markers,
        ),
        national_scope_markers=_get_tuple_of_str(
            data,
            "national_scope_markers",
            DEFAULT_EXTRACTOR_SCHEMA.national_scope_markers,
        ),
        score_weights={
            k: int(v)
            for k, v in _get_number_dict(
                data, "score_weights", DEFAULT_EXTRACTOR_SCHEMA.score_weights, as_int=True
            ).items()
        },
        search_positive_terms={
            k: int(v)
            for k, v in _get_number_dict(
                data,
                "search_positive_terms",
                DEFAULT_EXTRACTOR_SCHEMA.search_positive_terms,
                as_int=True,
            ).items()
        },
        search_negative_terms={
            k: int(v)
            for k, v in _get_number_dict(
                data,
                "search_negative_terms",
                DEFAULT_EXTRACTOR_SCHEMA.search_negative_terms,
                as_int=True,
            ).items()
        },
    )
    if not merged.unit_to_10k:
        raise ValueError("unit_to_10k must not be empty")
    return merged
