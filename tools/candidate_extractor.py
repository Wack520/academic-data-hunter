from __future__ import annotations

import functools
import re
from urllib.parse import urlparse

from tools.extractor_schema import DEFAULT_EXTRACTOR_SCHEMA, ExtractorSchema
from tools.province_mapper import PROVINCE_MAP, normalize

PROV_ALIAS = {
    "内蒙古自治区": ["内蒙古", "全区", "我区"],
    "吉林省": ["吉林", "全省", "我省"],
    "山西省": ["山西", "全省", "我省"],
    "新疆维吾尔自治区": ["新疆", "全区", "我区"],
    "江苏省": ["江苏", "全省", "我省"],
    "江西省": ["江西", "全省", "我省"],
    "湖北省": ["湖北", "全省", "我省"],
    "福建省": ["福建", "全省", "我省"],
    "辽宁省": ["辽宁", "全省", "我省"],
    "陕西省": ["陕西", "全省", "我省"],
    "青海省": ["青海", "全省", "我省"],
    "黑龙江省": ["黑龙江", "全省", "我省"],
}

PROV_URL_HINTS = {
    "内蒙古自治区": ["nmg", "neimenggu"],
    "吉林省": ["jilin", "jl.gov.cn"],
    "山西省": ["shanxi", "sx.gov.cn"],
    "新疆维吾尔自治区": ["xinjiang", "xj.gov.cn"],
    "江苏省": ["jiangsu", "js.gov.cn", "zgjssw", "jszx"],
    "江西省": ["jiangxi", "jx.gov.cn"],
    "湖北省": ["hubei", "hb.gov.cn"],
    "福建省": ["fujian", "fj.gov.cn"],
    "辽宁省": ["liaoning", "ln.gov.cn"],
    "陕西省": ["shaanxi", "sn.gov.cn", "sx.gov.cn"],
    "青海省": ["qinghai", "qh.gov.cn"],
    "黑龙江省": ["heilongjiang", "hlj.gov.cn"],
}

# Derive from the single source of truth (province_mapper.PROVINCE_MAP)
OTHER_PROV_HINTS: list[str] = list(PROVINCE_MAP.keys())


def _fallback_short_name(province: str) -> str:
    """Best-effort short name extraction for unknown entries."""
    for suffix in [
        "壮族自治区",
        "回族自治区",
        "维吾尔自治区",
        "自治区",
        "特别行政区",
        "省",
        "市",
    ]:
        if province.endswith(suffix):
            return province[: -len(suffix)]
    return province


@functools.lru_cache(maxsize=128)
def _province_alias(province: str) -> list[str]:
    """Resolve province alias and scope markers for all provinces, not only overrides."""
    if province in PROV_ALIAS:
        return PROV_ALIAS[province]

    try:
        short = normalize(province, "short")
        full = normalize(province, "full")
    except ValueError:
        short = _fallback_short_name(province)
        full = province

    markers: set[str] = set()
    if "自治区" in full:
        markers.update({"全区", "我区", "全省", "我省"})
    if full.endswith("市"):
        markers.update({"全市", "我市"})
    if full.endswith("省") and "自治区" not in full:
        markers.update({"全省", "我省"})
    if not markers:
        markers.update({"全省", "我省"})

    ordered_markers = ["全省", "我省", "全区", "我区", "全市", "我市"]
    return [short, *[marker for marker in ordered_markers if marker in markers]]


def _resolve_schema(schema: ExtractorSchema | None) -> ExtractorSchema:
    return schema or DEFAULT_EXTRACTOR_SCHEMA


def _weight(schema: ExtractorSchema, key: str, default: int = 0) -> int:
    return int(schema.score_weights.get(key, default))


def split_sentences(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text)
    return [item.strip() for item in re.split(r"(?<=[。！？；])", normalized) if item.strip()]


def extract_domain(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower()
    except Exception:
        return ""


def score_domain_quality(url: str) -> int:
    host = extract_domain(url)
    if not host:
        return 0
    score_value = 0
    if host.endswith(".gov.cn") or ".gov.cn" in host:
        score_value += 6
    if any(k in host for k in ["stats", "tjj", "mps", "ga", "gov"]):
        score_value += 2
    if any(k in host for k in ["weixin.qq.com", "toutiao", "sohu", "163.com", "baijiahao"]):
        score_value -= 3
    return score_value


def score(
    province: str,
    sentence: str,
    url: str,
    year: int = 2023,
    schema: ExtractorSchema | None = None,
) -> int:
    active_schema = _resolve_schema(schema)
    alias = _province_alias(province)
    explicit_name = alias[0]
    score_value = 0

    year_markers = active_schema.resolve_year_end_markers(year)
    if any(marker in sentence for marker in year_markers):
        score_value += _weight(active_schema, "year_end", 8)

    if any(marker in sentence for marker in active_schema.partial_year_markers):
        score_value += _weight(active_schema, "partial_year", 5)

    if any(marker in sentence for marker in active_schema.province_scope_markers):
        score_value += _weight(active_schema, "province_scope", 4)

    if explicit_name in sentence or province in sentence:
        score_value += _weight(active_schema, "explicit_province", 4)

    if any(marker in sentence for marker in active_schema.city_scope_markers):
        score_value += _weight(active_schema, "city_scope", -5)

    if any(marker in sentence for marker in active_schema.national_scope_markers):
        score_value += _weight(active_schema, "national_scope", -9)

    for province_keyword in OTHER_PROV_HINTS:
        if province_keyword == explicit_name:
            continue
        if province_keyword in sentence:
            score_value += _weight(active_schema, "other_province", -8)
            break

    lower_url = url.lower()
    if explicit_name not in sentence and province not in sentence:
        hints = PROV_URL_HINTS.get(province, [])
        if hints and any(hint in lower_url for hint in hints):
            score_value += _weight(active_schema, "url_hint", 2)

    return score_value


def _render_units_pattern(schema: ExtractorSchema) -> str:
    units = [re.escape(unit) for unit in schema.unit_to_10k if unit]
    if not units:
        return r"万辆|辆"
    return "|".join(units)


def _render_regex(pattern: str, schema: ExtractorSchema) -> str:
    return pattern.replace("{units}", f"(?:{_render_units_pattern(schema)})")


def _extract_value(sentence: str, schema: ExtractorSchema | None = None) -> tuple[float, str] | None:
    active_schema = _resolve_schema(schema)
    primary_pattern = _render_regex(active_schema.primary_pattern, active_schema)
    fallback_pattern = _render_regex(active_schema.fallback_pattern, active_schema)

    match = None
    for token in active_schema.value_tokens:
        pos = sentence.find(token)
        if pos < 0:
            continue
        tail = sentence[pos : pos + 90]
        match = re.search(primary_pattern, tail)
        if match:
            break
    if not match:
        match = re.search(fallback_pattern, sentence)
    if not match:
        return None
    return float(match.group(1)), match.group(2)


def extract_candidates(
    province: str,
    url: str,
    text: str,
    year: int = 2023,
    schema: ExtractorSchema | None = None,
) -> list[dict[str, object]]:
    active_schema = _resolve_schema(schema)
    alias = _province_alias(province)
    explicit_name = alias[0]
    lower_url = url.lower()

    out: list[dict[str, object]] = []
    for sentence in split_sentences(text):
        if active_schema.required_term and active_schema.required_term not in sentence:
            continue
        if active_schema.any_terms and not any(term in sentence for term in active_schema.any_terms):
            continue
        if any(term in sentence for term in active_schema.exclude_phrases):
            continue

        has_explicit_province = explicit_name in sentence or province in sentence
        has_generic_scope = any(alias_token in sentence for alias_token in alias[1:])
        if not (has_explicit_province or has_generic_scope):
            continue
        if not has_explicit_province:
            hints = PROV_URL_HINTS.get(province, [])
            if hints and not any(hint in lower_url for hint in hints):
                continue

        extracted = _extract_value(sentence, schema=active_schema)
        if extracted is None:
            continue
        value_raw, unit = extracted
        value_factor = float(active_schema.unit_to_10k.get(unit, 1.0))
        value_10k = value_raw * value_factor

        out.append(
            {
                "url": url,
                "sentence": sentence[:260],
                "value_raw": value_raw,
                "unit": unit,
                "value_10k": round(value_10k, 6),
                "score": score(province, sentence, url, year=year, schema=active_schema),
                "explicit_province_in_sentence": has_explicit_province,
            }
        )
    return out


def dedup(candidates: list[dict[str, object]]) -> list[dict[str, object]]:
    deduplicated: list[dict[str, object]] = []
    used: set[tuple[object, object, object]] = set()

    def sort_key(item: dict[str, object]) -> float:
        value = item.get("score", 0.0)
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(str(value))
        except (TypeError, ValueError):
            return 0.0

    for item in sorted(candidates, key=sort_key, reverse=True):
        key = (item.get("url"), item.get("value_10k"), item.get("sentence"))
        if key in used:
            continue
        used.add(key)
        deduplicated.append(item)
    return deduplicated


def score_search_result(
    province: str,
    year: int,
    title: str,
    snippet: str,
    schema: ExtractorSchema | None = None,
) -> int:
    active_schema = _resolve_schema(schema)
    text = f"{title} {snippet}"
    short = _province_alias(province)[0]
    score_value = 0

    if short in text or province in text:
        score_value += _weight(active_schema, "search_province", 4)

    for term, bonus in active_schema.search_positive_terms.items():
        marker = term.replace("{year}", str(year))
        if marker and marker in text:
            score_value += int(bonus)

    for term, penalty in active_schema.search_negative_terms.items():
        marker = term.replace("{year}", str(year))
        if marker and marker in text:
            score_value += int(penalty)

    if str(year) in text:
        score_value += _weight(active_schema, "search_year", 3)

    return score_value
