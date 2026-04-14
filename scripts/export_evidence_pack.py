#!/usr/bin/env python3
"""
Export an evidence-backed delivery bundle for research-agent runs.

Default outputs:
  - manifest.json
  - dataset.csv
  - source_registry.csv
  - evidence_records.jsonl
  - README.md
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from tools.io import load_csv
from tools.provenance import (
    build_registry_indexes,
    build_resolved_provenance,
    has_value,
    parse_csv_list,
    pick_registry_match,
)


def csv_fieldnames(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or [])


def write_csv(rows: list[dict[str, str]], path: Path, fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_evidence_record(
    row: dict[str, str],
    row_index: int,
    key_cols: list[str],
    value_cols: list[str],
    match_mode: str,
    registry_match: dict[str, str] | None,
) -> dict[str, object]:
    row_key = {col: (row.get(col) or "").strip() for col in key_cols}
    values = (
        {col: (row.get(col) or "").strip() for col in value_cols if (row.get(col) or "").strip()}
        if value_cols
        else {
            col: (value or "").strip()
            for col, value in row.items()
            if col not in set(key_cols)
            and col
            not in {
                "source_id",
                "source_level",
                "source_name",
                "source_url",
                "cross_check_url",
                "access_date",
                "note",
            }
            and (value or "").strip()
        }
    )
    provenance = build_resolved_provenance(row, match_mode=match_mode, registry_match=registry_match)
    return {
        "row_index": row_index,
        "row_key": row_key,
        "values": values,
        "provenance": provenance,
        "row": row,
    }


def export_evidence_pack(
    *,
    data_path: Path,
    registry_path: Path,
    output_dir: Path,
    variable: str = "",
    value_cols: list[str] | None = None,
    key_cols: list[str] | None = None,
) -> dict[str, object]:
    active_value_cols = list(value_cols or [])
    active_key_cols = list(key_cols or ["province", "year"])

    data_rows = load_csv(data_path)
    registry_rows = load_csv(registry_path)
    registry_filtered = [
        row for row in registry_rows if not variable or (row.get("variable") or "").strip() == variable
    ]
    registry_by_id, registry_by_tuple = build_registry_indexes(registry_filtered)

    evidence_records: list[dict[str, object]] = []
    match_counter: Counter[str] = Counter()
    source_level_counter: Counter[str] = Counter()

    for row_index, row in enumerate(data_rows, start=2):
        if not has_value(row, active_value_cols):
            continue
        match_mode, registry_match = pick_registry_match(row, registry_by_id, registry_by_tuple)
        evidence_record = build_evidence_record(
            row,
            row_index=row_index,
            key_cols=active_key_cols,
            value_cols=active_value_cols,
            match_mode=match_mode,
            registry_match=registry_match,
        )
        evidence_records.append(evidence_record)
        match_counter[match_mode] += 1
        level = str(evidence_record["provenance"].get("source_level", "")).strip()
        if level:
            source_level_counter[level] += 1

    output_dir.mkdir(parents=True, exist_ok=True)
    dataset_out = output_dir / "dataset.csv"
    registry_out = output_dir / "source_registry.csv"
    records_out = output_dir / "evidence_records.jsonl"
    manifest_out = output_dir / "manifest.json"
    readme_out = output_dir / "README.md"

    write_csv(data_rows, dataset_out, fieldnames=csv_fieldnames(data_path))
    write_csv(registry_filtered, registry_out, fieldnames=csv_fieldnames(registry_path))

    with records_out.open("w", encoding="utf-8") as f:
        for record in evidence_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    generated_at = datetime.now(UTC).isoformat()
    manifest = {
        "generated_at_utc": generated_at,
        "data_file": str(data_path),
        "registry_file": str(registry_path),
        "output_dir": str(output_dir),
        "variable_filter": variable,
        "key_columns": active_key_cols,
        "value_columns": active_value_cols,
        "total_dataset_rows": len(data_rows),
        "total_registry_rows": len(registry_rows),
        "registry_rows_in_scope": len(registry_filtered),
        "evidence_record_count": len(evidence_records),
        "match_summary": dict(match_counter),
        "source_level_summary": dict(source_level_counter),
        "unique_source_ids": sorted(
            {
                str(record["provenance"].get("resolved_source_id", "")).strip()
                for record in evidence_records
                if str(record["provenance"].get("resolved_source_id", "")).strip()
            }
        ),
        "files": {
            "dataset": dataset_out.name,
            "source_registry": registry_out.name,
            "evidence_records": records_out.name,
            "summary": readme_out.name,
        },
    }
    manifest_out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    readme_lines = [
        "# Evidence Pack",
        "",
        "This bundle is a provenance-first delivery artifact for a research-agent run.",
        "",
        "## Summary",
        "",
        f"- Generated at (UTC): {generated_at}",
        f"- Dataset rows: {len(data_rows)}",
        f"- Registry rows in scope: {len(registry_filtered)}",
        f"- Evidence records: {len(evidence_records)}",
        f"- Variable filter: `{variable or '(all)'}`",
        f"- Value columns: `{', '.join(active_value_cols) if active_value_cols else '(all non-empty fields)'}`",
        "",
        "## Match summary",
        "",
    ]
    for key in ("source_id", "source_tuple", "unmatched"):
        readme_lines.append(f"- {key}: {match_counter.get(key, 0)}")
    readme_lines.extend(
        [
            "",
            "## Files",
            "",
            "- `dataset.csv` — exported dataset copy",
            "- `source_registry.csv` — filtered registry copy used for provenance matching",
            "- `evidence_records.jsonl` — row-level evidence records with provenance context",
            "- `manifest.json` — machine-readable bundle metadata",
            "",
        ]
    )
    readme_out.write_text("\n".join(readme_lines) + "\n", encoding="utf-8")

    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export an evidence-backed delivery bundle")
    parser.add_argument("--data", required=True, help="Dataset CSV path")
    parser.add_argument("--registry", required=True, help="Source registry CSV path")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--variable", default="", help="Optional registry variable filter")
    parser.add_argument("--value-col", default="", help="Comma-separated value columns to treat as evidence targets")
    parser.add_argument("--key", default="province,year", help="Comma-separated key columns")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = export_evidence_pack(
        data_path=Path(args.data).resolve(),
        registry_path=Path(args.registry).resolve(),
        output_dir=Path(args.output_dir).resolve(),
        variable=(args.variable or "").strip(),
        value_cols=parse_csv_list(args.value_col),
        key_cols=parse_csv_list(args.key),
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
