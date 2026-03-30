from __future__ import annotations

import csv
import sys
from pathlib import Path

import pytest

from tools import panel_merger, province_mapper, qc_checker


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def test_province_mapper_helper_functions() -> None:
    assert province_mapper.short_to_full("北京") == "北京市"
    assert province_mapper.short_to_full("北京市") == "北京市"
    assert province_mapper.full_to_short("北京市") == "北京"
    assert province_mapper.full_to_short("北京") == "北京"
    assert len(province_mapper.get_all_provinces("short")) == 30
    assert len(province_mapper.get_all_provinces("full")) == 30
    assert len(province_mapper.get_all_provinces("code")) == 30

    with pytest.raises(ValueError):
        province_mapper.short_to_full("火星省")
    with pytest.raises(ValueError):
        province_mapper.full_to_short("火星省")
    with pytest.raises(ValueError):
        province_mapper.get_all_provinces("invalid")


def test_panel_merger_main_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    base_path = tmp_path / "base.csv"
    new_path = tmp_path / "new.csv"
    out_path = tmp_path / "out.csv"

    _write_csv(
        base_path,
        [
            {"province": "北京", "year": "2023", "x": "", "note": "a"},
            {"province": "上海", "year": "2023", "x": "", "note": "b"},
        ],
    )
    _write_csv(
        new_path,
        [
            {"province": "北京市", "year": "2023", "x": "99"},
            {"province": "上海市", "year": "2023", "x": "88"},
        ],
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "panel_merger.py",
            "--base",
            str(base_path),
            "--new",
            str(new_path),
            "--on",
            "province,year",
            "--cols",
            "x",
            "--map-province",
            "short",
            "--output",
            str(out_path),
        ],
    )
    panel_merger.main()

    merged_rows = panel_merger.load_csv(str(out_path))
    assert [r["x"] for r in merged_rows] == ["99", "88"]


def test_qc_checker_validate_rows_and_main_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bad_rows = [
        {"province": "", "year": "2023", "value": "10", "source_url": ""},
        {"province": "北京", "year": "", "value": "11", "source_url": "https://example.gov.cn"},
    ]
    input_issues = qc_checker.validate_input_rows(bad_rows)
    assert len(input_issues) == 2

    bad_csv = tmp_path / "bad.csv"
    _write_csv(
        bad_csv,
        [
            {"province": "北京", "year": "2023", "value": "1万台", "source_url": ""},
            {"province": "北京", "year": "2023", "value": "5", "source_url": "https://a.gov.cn"},
        ],
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_checker.py",
            str(bad_csv),
            "--key",
            "province,year",
            "--required",
            "source_url",
            "--value-col",
            "value",
            "--check-unit",
            "台",
        ],
    )
    with pytest.raises(SystemExit) as exc:
        qc_checker.main()
    assert exc.value.code == 1

    good_csv = tmp_path / "good.csv"
    _write_csv(
        good_csv,
        [
            {"province": "北京", "year": "2023", "value": "10", "source_url": "https://a.gov.cn"},
            {"province": "上海", "year": "2023", "value": "11", "source_url": "https://b.gov.cn"},
        ],
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "qc_checker.py",
            str(good_csv),
            "--key",
            "province,year",
            "--required",
            "source_url",
            "--value-col",
            "value",
            "--check-unit",
            "台",
        ],
    )
    qc_checker.main()
