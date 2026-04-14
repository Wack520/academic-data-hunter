from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.run_benchmark_eval import run_benchmark_eval


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_run_benchmark_eval_reports_high_provenance_quality_with_registry_fallback(tmp_path: Path) -> None:
    data_path = tmp_path / "panel.csv"
    registry_path = tmp_path / "registry.csv"
    json_path = tmp_path / "benchmark.json"
    md_path = tmp_path / "benchmark.md"

    _write_csv(
        data_path,
        [
            {
                "province": "北京",
                "year": "2023",
                "target_value": "100",
                "source_id": "SRC_1",
                "source_level": "A",
                "source_name": "北京市统计局",
                "source_url": "https://a.gov.cn",
                "cross_check_url": "",
                "access_date": "2026-04-14",
                "note": "",
            },
            {
                "province": "天津",
                "year": "2023",
                "target_value": "200",
                "source_id": "",
                "source_level": "C",
                "source_name": "天津观察",
                "source_url": "https://news.example.com/tj",
                "cross_check_url": "",
                "access_date": "2026-04-14",
                "note": "",
            },
            {
                "province": "上海",
                "year": "2023",
                "target_value": "",
                "source_id": "",
                "source_level": "",
                "source_name": "",
                "source_url": "",
                "cross_check_url": "",
                "access_date": "",
                "note": "",
            },
        ],
    )
    _write_csv(
        registry_path,
        [
            {
                "source_id": "SRC_1",
                "variable": "target",
                "source_level": "A",
                "source_name": "北京市统计局",
                "source_url": "https://a.gov.cn",
                "cross_check_url": "",
                "publish_date": "",
                "access_date": "2026-04-14",
                "evidence_file": "",
                "is_primary": "1",
                "note": "",
            },
            {
                "source_id": "SRC_2",
                "variable": "target",
                "source_level": "C",
                "source_name": "天津观察",
                "source_url": "https://news.example.com/tj",
                "cross_check_url": "https://tj.gov.cn/cross",
                "publish_date": "",
                "access_date": "2026-04-14",
                "evidence_file": "",
                "is_primary": "0",
                "note": "",
            },
        ],
    )

    report = run_benchmark_eval(
        data_path=data_path,
        registry_path=registry_path,
        variable="target",
        value_cols=["target_value"],
        key_cols=["province", "year"],
        year_start=2023,
        year_end=2023,
        json_output=json_path,
        md_output=md_path,
    )

    assert report["counts"]["expected_key_count"] == 30
    assert report["counts"]["filled_key_count"] == 2
    assert report["metrics"]["registry_match_rate"] == 100.0
    assert report["metrics"]["c_cross_check_rate"] == 100.0
    assert report["metrics"]["source_quality_score"] == 70.0
    assert report["distributions"]["source_level"] == {"A": 1, "C": 1}
    assert report["metrics"]["overall_score"] > 60.0
    assert (
        json.loads(json_path.read_text(encoding="utf-8"))["metrics"]["overall_score"]
        == report["metrics"]["overall_score"]
    )
    assert "# Benchmark Eval Report" in md_path.read_text(encoding="utf-8")


def test_run_benchmark_eval_reports_low_score_for_unmatched_c_source(tmp_path: Path) -> None:
    data_path = tmp_path / "panel.csv"
    registry_path = tmp_path / "registry.csv"
    json_path = tmp_path / "benchmark.json"
    md_path = tmp_path / "benchmark.md"

    _write_csv(
        data_path,
        [
            {
                "province": "广东",
                "year": "2023",
                "target_value": "8",
                "source_id": "",
                "source_level": "C",
                "source_name": "某研究站",
                "source_url": "https://bad.example.com",
                "cross_check_url": "",
                "access_date": "",
                "note": "",
            }
        ],
    )
    _write_csv(
        registry_path,
        [
            {
                "source_id": "SRC_9",
                "variable": "other",
                "source_level": "A",
                "source_name": "其他来源",
                "source_url": "https://other.example.com",
                "cross_check_url": "",
                "publish_date": "",
                "access_date": "2026-04-14",
                "evidence_file": "",
                "is_primary": "0",
                "note": "",
            }
        ],
    )

    report = run_benchmark_eval(
        data_path=data_path,
        registry_path=registry_path,
        variable="target",
        value_cols=["target_value"],
        key_cols=["province", "year"],
        year_start=2023,
        year_end=2023,
        json_output=json_path,
        md_output=md_path,
    )

    assert report["metrics"]["registry_match_rate"] == 0.0
    assert report["metrics"]["c_cross_check_rate"] == 0.0
    assert report["metrics"]["provenance_completeness_rate"] == 60.0
    assert report["metrics"]["source_quality_score"] == 40.0
    assert report["metrics"]["overall_score"] < 30.0
