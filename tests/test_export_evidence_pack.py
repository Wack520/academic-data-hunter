from __future__ import annotations

import csv
import json
from pathlib import Path

from scripts.export_evidence_pack import export_evidence_pack


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_export_evidence_pack_matches_registry_by_source_id(tmp_path: Path) -> None:
    data_path = tmp_path / "panel.csv"
    registry_path = tmp_path / "registry.csv"
    out_dir = tmp_path / "evidence"

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
                "source_url": "https://example.gov.cn/a",
                "cross_check_url": "",
                "access_date": "2026-04-14",
                "note": "official",
            },
            {
                "province": "天津",
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
                "source_url": "https://example.gov.cn/a",
                "cross_check_url": "",
                "publish_date": "2026-01-01",
                "access_date": "2026-04-14",
                "evidence_file": "",
                "is_primary": "1",
                "note": "registry-note",
            }
        ],
    )

    manifest = export_evidence_pack(
        data_path=data_path,
        registry_path=registry_path,
        output_dir=out_dir,
        variable="target",
        value_cols=["target_value"],
        key_cols=["province", "year"],
    )

    assert manifest["evidence_record_count"] == 1
    assert manifest["match_summary"]["source_id"] == 1
    assert (out_dir / "dataset.csv").exists()
    assert (out_dir / "source_registry.csv").exists()
    assert (out_dir / "evidence_records.jsonl").exists()
    assert (out_dir / "manifest.json").exists()
    assert (out_dir / "README.md").exists()

    record = json.loads((out_dir / "evidence_records.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert record["row_key"] == {"province": "北京", "year": "2023"}
    assert record["values"] == {"target_value": "100"}
    assert record["provenance"]["match_mode"] == "source_id"
    assert record["provenance"]["registry_record"]["note"] == "registry-note"


def test_export_evidence_pack_falls_back_to_source_tuple_match(tmp_path: Path) -> None:
    data_path = tmp_path / "panel.csv"
    registry_path = tmp_path / "registry.csv"
    out_dir = tmp_path / "evidence"

    _write_csv(
        data_path,
        [
            {
                "province": "上海",
                "year": "2023",
                "target_value": "88",
                "source_id": "",
                "source_level": "B",
                "source_name": "上海年鉴",
                "source_url": "https://example.com/yearbook",
                "cross_check_url": "",
                "access_date": "2026-04-14",
                "note": "",
            }
        ],
    )
    _write_csv(
        registry_path,
        [
            {
                "source_id": "SRC_2",
                "variable": "target",
                "source_level": "B",
                "source_name": "上海年鉴",
                "source_url": "https://example.com/yearbook",
                "cross_check_url": "https://example.com/cross",
                "publish_date": "",
                "access_date": "2026-04-14",
                "evidence_file": "",
                "is_primary": "0",
                "note": "",
            }
        ],
    )

    manifest = export_evidence_pack(
        data_path=data_path,
        registry_path=registry_path,
        output_dir=out_dir,
        variable="target",
        value_cols=["target_value"],
        key_cols=["province", "year"],
    )

    assert manifest["match_summary"]["source_tuple"] == 1
    assert manifest["unique_source_ids"] == ["SRC_2"]
    record = json.loads((out_dir / "evidence_records.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert record["provenance"]["match_mode"] == "source_tuple"
    assert record["provenance"]["resolved_source_id"] == "SRC_2"
    assert record["provenance"]["registry_record"]["cross_check_url"] == "https://example.com/cross"
