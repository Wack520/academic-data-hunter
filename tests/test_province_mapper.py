import pytest

from tools.province_mapper import normalize


def test_normalize_short_and_full_name():
    assert normalize("北京", "short") == "北京"
    assert normalize("北京市", "short") == "北京"
    assert normalize("北京", "full") == "北京市"


def test_normalize_adcode_and_fuzzy_match():
    assert normalize("110000", "short") == "北京"
    assert normalize("北京市朝阳区", "short") == "北京"
    assert normalize("广西壮族自治区", "code") == "450000"


def test_normalize_invalid_province_and_target():
    with pytest.raises(ValueError):
        normalize("火星省", "short")
    with pytest.raises(ValueError):
        normalize("北京", "oops")


@pytest.mark.parametrize("bad_input", [None, 123])
def test_normalize_abnormal_input_raises(bad_input):
    with pytest.raises((AttributeError, TypeError, ValueError)):
        normalize(bad_input, "short")
