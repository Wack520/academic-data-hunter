from __future__ import annotations

import re
from urllib.parse import urlparse

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

OTHER_PROV_HINTS = [
    "北京",
    "天津",
    "河北",
    "山西",
    "内蒙古",
    "辽宁",
    "吉林",
    "黑龙江",
    "上海",
    "江苏",
    "浙江",
    "安徽",
    "福建",
    "江西",
    "山东",
    "河南",
    "湖北",
    "湖南",
    "广东",
    "广西",
    "海南",
    "重庆",
    "四川",
    "贵州",
    "云南",
    "陕西",
    "甘肃",
    "青海",
    "宁夏",
    "新疆",
]


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


def score(province: str, sentence: str, url: str, year: int = 2023) -> int:
    alias = PROV_ALIAS.get(province, [province.replace("省", "").replace("市", "")])
    explicit_name = alias[0]
    score_value = 0
    year_markers = [
        f"截至{year}年底",
        f"{year}年底",
        f"{year}年末",
        "截至去年底",
        "截至去年末",
    ]
    if any(marker in sentence for marker in year_markers):
        score_value += 8
    if any(marker in sentence for marker in ["截至11月底", "截至10月底", "截至9月底", "截至今年9月30日"]):
        score_value += 5
    if any(marker in sentence for marker in ["全省", "全区", "我省", "我区"]):
        score_value += 4
    if explicit_name in sentence or province in sentence:
        score_value += 4
    if "全市" in sentence:
        score_value -= 5
    if "全国" in sentence:
        score_value -= 9
    for prov_keyword in OTHER_PROV_HINTS:
        if prov_keyword == explicit_name:
            continue
        if prov_keyword in sentence:
            score_value -= 8
            break

    url_l = url.lower()
    if explicit_name not in sentence and province not in sentence:
        hints = PROV_URL_HINTS.get(province, [])
        if hints and any(hint in url_l for hint in hints):
            score_value += 2

    return score_value


def _extract_value(sentence: str) -> tuple[float, str] | None:
    match = None
    for token in ["新能源汽车保有量", "新能源车保有量", "电动汽车保有量"]:
        pos = sentence.find(token)
        if pos < 0:
            continue
        tail = sentence[pos : pos + 90]
        match = re.search(r"(?:达到|达|为|约为|突破)?\s*([0-9]+(?:\.[0-9]+)?)\s*(万辆|辆)", tail)
        if match:
            break
    if not match:
        match = re.search(
            r"(?:新能源汽车|新能源车|电动汽车)[^。；，,]{0,40}(?:保有量)?[^0-9]{0,12}([0-9]+(?:\.[0-9]+)?)\s*(万辆|辆)",
            sentence,
        )
    if not match:
        return None
    return float(match.group(1)), match.group(2)


def extract_candidates(province: str, url: str, text: str, year: int = 2023) -> list[dict[str, object]]:
    alias = PROV_ALIAS.get(province, [province.replace("省", "").replace("市", "")])
    explicit_name = alias[0]
    url_l = url.lower()

    out: list[dict[str, object]] = []
    for sentence in split_sentences(text):
        if "保有量" not in sentence:
            continue
        if "新能源" not in sentence and "电动汽车" not in sentence:
            continue
        if "全国新能源汽车保有量" in sentence:
            continue

        has_explicit_province = explicit_name in sentence or province in sentence
        has_generic_scope = any(alias_token in sentence for alias_token in alias[1:])
        if not (has_explicit_province or has_generic_scope):
            continue
        if not has_explicit_province:
            hints = PROV_URL_HINTS.get(province, [])
            if hints and not any(h in url_l for h in hints):
                continue

        extracted = _extract_value(sentence)
        if extracted is None:
            continue
        value_raw, unit = extracted
        value_10k = value_raw if unit == "万辆" else value_raw * 0.0001

        out.append(
            {
                "url": url,
                "sentence": sentence[:260],
                "value_raw": value_raw,
                "unit": unit,
                "value_10k": round(value_10k, 6),
                "score": score(province, sentence, url, year=year),
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


def score_search_result(province: str, year: int, title: str, snippet: str) -> int:
    text = f"{title} {snippet}"
    short = PROV_ALIAS.get(province, [province.replace("省", "").replace("市", "")])[0]
    score_value = 0
    if short in text or province in text:
        score_value += 4
    if "保有量" in text:
        score_value += 4
    if "新能源" in text:
        score_value += 3
    if str(year) in text:
        score_value += 3
    if "统计公报" in text or "政府" in text or "公安" in text:
        score_value += 3
    if "国民经济和社会发展" in text:
        score_value += 2
    if "全国" in text:
        score_value -= 4
    if "全市" in text or "某市" in text:
        score_value -= 3
    return score_value
