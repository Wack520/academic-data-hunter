import copy

import pytest

from tools.panel_merger import merge_panel


@pytest.fixture
def base_rows():
    return [
        {"province": "北京", "year": "2023", "x": "", "note": "a"},
        {"province": "上海", "year": "2023", "x": "", "note": "b"},
    ]


def test_merge_panel_basic_fill(base_rows):
    new_rows = [
        {"province": "北京", "year": "2023", "x": "100"},
        {"province": "上海", "year": "2023", "x": "200"},
    ]
    merged_rows, merged_count = merge_panel(copy.deepcopy(base_rows), new_rows, ["province", "year"], ["x"])
    assert merged_count == 2
    assert [r["x"] for r in merged_rows] == ["100", "200"]


def test_merge_panel_with_province_mapping(base_rows):
    new_rows = [
        {"province": "北京市", "year": "2023", "x": "300"},
        {"province": "上海市", "year": "2023", "x": "400"},
    ]
    merged_rows, merged_count = merge_panel(
        copy.deepcopy(base_rows), new_rows, ["province", "year"], ["x"], province_target="short"
    )
    assert merged_count == 2
    assert [r["x"] for r in merged_rows] == ["300", "400"]


def test_merge_panel_duplicate_key_in_new_rows_last_one_wins(base_rows):
    new_rows = [
        {"province": "北京", "year": "2023", "x": "111"},
        {"province": "北京", "year": "2023", "x": "222"},
    ]
    merged_rows, merged_count = merge_panel(copy.deepcopy(base_rows), new_rows, ["province", "year"], ["x"])
    assert merged_count == 1
    beijing = next(r for r in merged_rows if r["province"] == "北京")
    assert beijing["x"] == "222"


def test_merge_panel_empty_new_value_does_not_override(base_rows):
    seeded = copy.deepcopy(base_rows)
    seeded[0]["x"] = "old"
    new_rows = [{"province": "北京", "year": "2023", "x": ""}]
    merged_rows, merged_count = merge_panel(seeded, new_rows, ["province", "year"], ["x"])
    assert merged_count == 0
    assert merged_rows[0]["x"] == "old"
