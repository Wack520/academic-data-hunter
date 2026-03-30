import pytest

from tools.qc_checker import check_required, check_uniqueness, check_unit


@pytest.fixture
def sample_rows():
    return [
        {"province": "北京", "year": "2023", "value": "10", "source_url": "https://a.gov.cn"},
        {"province": "北京", "year": "2023", "value": "11", "source_url": "https://b.gov.cn"},
        {"province": "上海", "year": "2023", "value": "", "source_url": ""},
        {"province": "广东", "year": "2023", "value": "9", "source_url": ""},
    ]


def test_check_uniqueness_detects_duplicates(sample_rows):
    dupes = check_uniqueness(sample_rows, ["province", "year"])
    assert dupes[("北京", "2023")] == 2


def test_check_required_with_value_cols_only_checks_non_empty_values(sample_rows):
    issues = check_required(sample_rows, ["source_url"], value_cols=["value"])
    assert len(issues) == 1
    line, prov, year, col = issues[0]
    assert (line, prov, year, col) == (5, "广东", "2023", "source_url")


def test_check_required_without_value_cols_checks_all_rows(sample_rows):
    issues = check_required(sample_rows, ["source_url"], value_cols=None)
    # 上海 + 广东 两行都缺 source_url
    assert {(x[1], x[2], x[3]) for x in issues} == {("上海", "2023", "source_url"), ("广东", "2023", "source_url")}


def test_check_unit_branches():
    rows = [
        {"province": "北京", "year": "2023", "v": "123"},          # 纯数字通过
        {"province": "上海", "year": "2023", "v": "1.2万台"},      # 万/亿异常
        {"province": "广东", "year": "2023", "v": "500辆"},       # 单位不匹配
        {"province": "江苏", "year": "2023", "v": "600台"},       # 正确单位
        {"province": "浙江", "year": "2023", "v": "1.2e3"},      # 科学计数通过
    ]
    issues = check_unit(rows, ["v"], expected_unit="台")
    assert len(issues) == 2
    reasons = {x[-1] for x in issues}
    assert "包含万/亿等未换算单位" in reasons
    assert "单位疑似不为台" in reasons
