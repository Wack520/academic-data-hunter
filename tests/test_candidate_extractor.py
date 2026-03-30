"""Tests for tools.candidate_extractor — score / extract / dedup logic."""

from __future__ import annotations

import pytest

from tools.candidate_extractor import (
    _extract_value,
    dedup,
    extract_candidates,
    extract_domain,
    score,
    score_domain_quality,
    score_search_result,
    split_sentences,
)

# ── split_sentences ──────────────────────────────────────────────


class TestSplitSentences:
    def test_basic_chinese_punctuation(self):
        text = "第一句。第二句！第三句？"
        result = split_sentences(text)
        assert len(result) == 3
        assert result[0] == "第一句。"
        assert result[1] == "第二句！"

    def test_whitespace_normalization(self):
        text = "第一句。    第二句\n\n第三句。"
        result = split_sentences(text)
        # whitespace collapsed
        assert all("  " not in s for s in result)

    def test_empty_string(self):
        assert split_sentences("") == []


# ── extract_domain ────────────────────────────────────────────────


class TestExtractDomain:
    def test_normal_url(self):
        assert extract_domain("https://www.stats.gov.cn/page") == "www.stats.gov.cn"

    def test_invalid_url(self):
        assert extract_domain("not a url") == ""

    def test_empty_string(self):
        assert extract_domain("") == ""


# ── score_domain_quality ──────────────────────────────────────────


class TestScoreDomainQuality:
    def test_gov_cn_gets_high_score(self):
        s = score_domain_quality("https://www.hubei.gov.cn/data")
        assert s >= 6

    def test_stats_gov_gets_extra(self):
        s = score_domain_quality("https://tjj.hubei.gov.cn/data")
        assert s >= 8  # gov.cn(6) + stats/tjj(2)

    def test_social_media_penalized(self):
        s = score_domain_quality("https://baijiahao.baidu.com/article")
        assert s < 0

    def test_empty_url_returns_zero(self):
        assert score_domain_quality("") == 0


# ── score ─────────────────────────────────────────────────────────


class TestScore:
    """Test the core per-sentence scoring function."""

    def test_year_end_marker_high_score(self):
        sentence = "截至2023年底，湖北省新能源汽车保有量达100万辆"
        s = score("湖北省", sentence, "https://hubei.gov.cn/", year=2023)
        assert s >= 12  # year marker(8) + province(4)

    def test_province_mention_gives_points(self):
        s = score("湖北省", "湖北新能源汽车保有量达100万辆", "", year=2023)
        assert s >= 4

    def test_nationwide_penalty(self):
        s = score("湖北省", "全国新能源汽车保有量达2000万辆", "", year=2023)
        assert s < 0  # -9 for 全国

    def test_city_level_penalty(self):
        s = score("湖北省", "全市新能源汽车保有量达50万辆", "", year=2023)
        assert s < 0  # -5 for 全市

    def test_other_province_penalty(self):
        sentence = "广东省新能源汽车保有量达200万辆"
        s = score("湖北省", sentence, "", year=2023)
        assert s < 0  # -8 for mentioning another province

    def test_url_hint_boost(self):
        """URL containing province pinyin adds score when province not in sentence."""
        s = score("湖北省", "全省新能源汽车保有量达100万辆", "https://hubei.gov.cn/data", year=2023)
        assert s >= 6  # 全省(4) + url hint(2)

    @pytest.mark.parametrize(
        "province",
        ["内蒙古自治区", "吉林省", "山西省", "新疆维吾尔自治区", "江苏省", "黑龙江省"],
    )
    def test_alias_provinces(self, province):
        """Ensure aliased provinces get matched via their short name."""
        short = province.replace("省", "").replace("自治区", "").replace("维吾尔", "")
        sentence = f"截至2023年底，{short}新能源汽车保有量达50万辆"
        s = score(province, sentence, "", year=2023)
        assert s >= 8  # year marker + province name

    def test_partial_year_marker(self):
        sentence = "截至11月底，全省新能源汽车保有量达80万辆"
        s = score("湖北省", sentence, "", year=2023)
        assert s >= 9  # partial year(5) + 全省(4)


# ── _extract_value ────────────────────────────────────────────────


class TestExtractValue:
    def test_wan_liang_unit(self):
        sentence = "新能源汽车保有量达到123.4万辆"
        result = _extract_value(sentence)
        assert result is not None
        value, unit = result
        assert value == 123.4
        assert unit == "万辆"

    def test_liang_unit(self):
        sentence = "新能源汽车保有量为56789辆"
        result = _extract_value(sentence)
        assert result is not None
        value, unit = result
        assert value == 56789
        assert unit == "辆"

    def test_electric_vehicle_variant(self):
        sentence = "电动汽车保有量突破100万辆"
        result = _extract_value(sentence)
        assert result is not None
        assert result[0] == 100

    def test_no_match_returns_none(self):
        assert _extract_value("今天天气不错") is None

    def test_no_number_returns_none(self):
        assert _extract_value("新能源汽车保有量持续增长") is None


# ── extract_candidates ────────────────────────────────────────────


class TestExtractCandidates:
    def test_basic_extraction(self):
        text = "截至2023年底，湖北省新能源汽车保有量达到67.8万辆。另有其他信息。"
        results = extract_candidates("湖北省", "https://hubei.gov.cn/data", text, year=2023)
        assert len(results) == 1
        assert results[0]["value_10k"] == 67.8  # already 万辆
        assert results[0]["url"] == "https://hubei.gov.cn/data"
        assert results[0]["score"] > 0

    def test_liang_to_wan_conversion(self):
        text = "截至2023年底，湖北省新能源汽车保有量为500000辆。"
        results = extract_candidates("湖北省", "https://example.com", text, year=2023)
        assert len(results) == 1
        assert results[0]["value_10k"] == pytest.approx(50.0, rel=1e-3)

    def test_filters_nationwide_data(self):
        text = "全国新能源汽车保有量达2000万辆。湖北省共有50万辆。"
        results = extract_candidates("湖北省", "https://example.com", text, year=2023)
        # "全国新能源汽车保有量" line should be filtered out
        assert all("全国" not in r.get("sentence", "") for r in results)

    def test_no_match_returns_empty(self):
        text = "今天阳光明媚，适合出行。"
        assert extract_candidates("湖北省", "https://example.com", text) == []

    def test_requires_province_context(self):
        """Sentence with 保有量 but no province reference should not match."""
        text = "截至2023年底，新能源汽车保有量达到100万辆。"
        results = extract_candidates("湖北省", "https://example.com", text, year=2023)
        assert results == []


# ── dedup ─────────────────────────────────────────────────────────


class TestDedup:
    def test_removes_exact_duplicates(self):
        items = [
            {"url": "a.com", "value_10k": 1.0, "sentence": "s1", "score": 10},
            {"url": "a.com", "value_10k": 1.0, "sentence": "s1", "score": 5},
        ]
        result = dedup(items)
        assert len(result) == 1
        assert result[0]["score"] == 10  # keeps higher score

    def test_keeps_different_values(self):
        items = [
            {"url": "a.com", "value_10k": 1.0, "sentence": "s1", "score": 10},
            {"url": "a.com", "value_10k": 2.0, "sentence": "s2", "score": 8},
        ]
        result = dedup(items)
        assert len(result) == 2

    def test_empty_input(self):
        assert dedup([]) == []

    def test_sort_by_score_descending(self):
        items = [
            {"url": "a.com", "value_10k": 1.0, "sentence": "s1", "score": 3},
            {"url": "b.com", "value_10k": 2.0, "sentence": "s2", "score": 9},
            {"url": "c.com", "value_10k": 3.0, "sentence": "s3", "score": 6},
        ]
        result = dedup(items)
        scores = [r["score"] for r in result]
        assert scores == [9, 6, 3]


# ── score_search_result ───────────────────────────────────────────


class TestScoreSearchResult:
    def test_ideal_result_high_score(self):
        s = score_search_result("湖北省", 2023, "湖北省2023年新能源汽车保有量统计公报", "湖北新能源汽车保有量达67万辆")
        assert s >= 14  # province(4) + 保有量(4) + 新能源(3) + year(3) + 统计公报(3)

    def test_nationwide_penalty(self):
        s = score_search_result("湖北省", 2023, "全国新能源汽车保有量", "全国数据")
        assert s < 10  # -4 for 全国

    def test_city_level_penalty(self):
        s = score_search_result("湖北省", 2023, "某市新能源车数据", "全市充电桩")
        assert s < 5  # -3 for 全市/某市
