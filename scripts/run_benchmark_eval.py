#!/usr/bin/env python3
"""
Run a benchmark/eval report for a research-data run.
"""

from __future__ import annotations

import argparse
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
from tools.province_mapper import PROVINCE_MAP, normalize

SOURCE_QUALITY_SCORES = {"A": 100.0, "B": 70.0, "C": 40.0}
COMPOSITE_WEIGHTS = {
    "fill_rate": 0.35,
    "provenance_completeness_rate": 0.20,
    "registry_match_rate": 0.20,
    "source_quality_score": 0.15,
    "c_cross_check_rate": 0.10,
}


def _norm_value_for_key(col: str, raw: str) -> str:
    value = (raw or "").strip()
    if col == "province" and value:
        try:
            return normalize(value, "short")
        except ValueError:
            return value
    if col == "year" and value.isdigit():
        return str(int(value))
    return value


def _row_key(row: dict[str, str], key_cols: list[str]) -> tuple[str, ...]:
    return tuple(_norm_value_for_key(col, row.get(col) or "") for col in key_cols)


def _expected_key_count(
    rows: list[dict[str, str]],
    key_cols: list[str],
    year_start: int | None,
    year_end: int | None,
) -> int:
    if set(key_cols) == {"province", "year"} and year_start is not None and year_end is not None:
        return len(PROVINCE_MAP) * max(0, year_end - year_start + 1)
    return len({_row_key(row, key_cols) for row in rows})


def _provenance_completeness(provenance: dict[str, object]) -> float:
    required_fields = [
        "resolved_source_id",
        "resolved_source_level",
        "resolved_source_name",
        "resolved_source_url",
        "access_date",
    ]
    present = sum(1 for field in required_fields if str(provenance.get(field, "")).strip())
    return round(present / len(required_fields) * 100, 4)


def _cross_check_present(provenance: dict[str, object]) -> bool:
    raw = str(provenance.get("cross_check_url", "")).strip()
    if raw:
        return True
    registry_record = provenance.get("registry_record", {})
    if isinstance(registry_record, dict):
        return bool(str(registry_record.get("cross_check_url", "")).strip())
    return False


def _source_quality_score(source_levels: list[str]) -> float:
    if not source_levels:
        return 0.0
    total = sum(SOURCE_QUALITY_SCORES.get(level, 0.0) for level in source_levels)
    return round(total / len(source_levels), 4)


def _overall_score(metrics: dict[str, float]) -> float:
    total = 0.0
    for key, weight in COMPOSITE_WEIGHTS.items():
        total += float(metrics.get(key, 0.0)) * weight
    return round(total, 4)


def _build_markdown(report: dict[str, object]) -> str:
    metrics = report["metrics"]
    counts = report["counts"]
    distributions = report["distributions"]
    lines = [
        "# Benchmark Eval Report",
        "",
        f"- Generated at (UTC): {report['generated_at_utc']}",
        f"- Variable filter: `{report['variable_filter'] or '(all)'}`",
        f"- Value columns: `{', '.join(report['value_columns']) if report['value_columns'] else '(all)'}`",
        "",
        "## Counts",
        "",
        f"- Expected keys: {counts['expected_key_count']}",
        f"- Filled keys: {counts['filled_key_count']}",
        f"- Filled rows: {counts['filled_row_count']}",
        f"- Registry rows in scope: {counts['registry_rows_in_scope']}",
        "",
        "## Metrics",
        "",
        f"- Fill rate: {metrics['fill_rate']:.2f}",
        f"- Provenance completeness rate: {metrics['provenance_completeness_rate']:.2f}",
        f"- Registry match rate: {metrics['registry_match_rate']:.2f}",
        f"- C-level cross-check rate: {metrics['c_cross_check_rate']:.2f}",
        f"- Source quality score: {metrics['source_quality_score']:.2f}",
        f"- Overall score: {metrics['overall_score']:.2f}",
        "",
        "## Distributions",
        "",
        f"- Source levels: {json.dumps(distributions['source_level'], ensure_ascii=False)}",
        f"- Match modes: {json.dumps(distributions['match_mode'], ensure_ascii=False)}",
        "",
    ]
    return "\n".join(lines)


def run_benchmark_eval(
    *,
    data_path: Path,
    registry_path: Path,
    variable: str = "",
    value_cols: list[str] | None = None,
    key_cols: list[str] | None = None,
    year_start: int | None = None,
    year_end: int | None = None,
    json_output: Path | None = None,
    md_output: Path | None = None,
) -> dict[str, object]:
    active_value_cols = list(value_cols or [])
    active_key_cols = list(key_cols or ["province", "year"])

    data_rows = load_csv(data_path)
    registry_rows = load_csv(registry_path)
    registry_filtered = [
        row for row in registry_rows if not variable or (row.get("variable") or "").strip() == variable
    ]
    registry_by_id, registry_by_tuple = build_registry_indexes(registry_filtered)

    filled_rows: list[dict[str, str]] = []
    filled_keys: set[tuple[str, ...]] = set()
    provenance_scores: list[float] = []
    source_levels: list[str] = []
    c_cross_checks: list[bool] = []
    match_counter: Counter[str] = Counter()
    source_level_counter: Counter[str] = Counter()

    for row in data_rows:
        if not has_value(row, active_value_cols):
            continue
        filled_rows.append(row)
        filled_keys.add(_row_key(row, active_key_cols))
        match_mode, registry_match = pick_registry_match(row, registry_by_id, registry_by_tuple)
        provenance = build_resolved_provenance(row, match_mode=match_mode, registry_match=registry_match)
        provenance_scores.append(_provenance_completeness(provenance))
        match_counter[match_mode] += 1

        resolved_level = str(provenance.get("resolved_source_level", "")).strip()
        if resolved_level:
            source_levels.append(resolved_level)
            source_level_counter[resolved_level] += 1
            if resolved_level == "C":
                c_cross_checks.append(_cross_check_present(provenance))

    expected_key_count = _expected_key_count(data_rows, active_key_cols, year_start=year_start, year_end=year_end)
    filled_key_count = len(filled_keys)
    filled_row_count = len(filled_rows)
    registry_match_count = filled_row_count - match_counter.get("unmatched", 0)

    metrics = {
        "fill_rate": round((filled_key_count / expected_key_count * 100) if expected_key_count else 0.0, 4),
        "provenance_completeness_rate": round(
            (sum(provenance_scores) / len(provenance_scores)) if provenance_scores else 0.0,
            4,
        ),
        "registry_match_rate": round((registry_match_count / filled_row_count * 100) if filled_row_count else 0.0, 4),
        "c_cross_check_rate": round(
            (sum(1 for ok in c_cross_checks if ok) / len(c_cross_checks) * 100) if c_cross_checks else 100.0,
            4,
        ),
        "source_quality_score": _source_quality_score(source_levels),
    }
    metrics["overall_score"] = _overall_score(metrics)

    report = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "data_file": str(data_path),
        "registry_file": str(registry_path),
        "variable_filter": variable,
        "key_columns": active_key_cols,
        "value_columns": active_value_cols,
        "counts": {
            "data_row_count": len(data_rows),
            "registry_row_count": len(registry_rows),
            "registry_rows_in_scope": len(registry_filtered),
            "data_unique_key_count": len({_row_key(row, active_key_cols) for row in data_rows}),
            "expected_key_count": expected_key_count,
            "filled_key_count": filled_key_count,
            "filled_row_count": filled_row_count,
        },
        "distributions": {
            "source_level": dict(source_level_counter),
            "match_mode": dict(match_counter),
        },
        "metrics": metrics,
    }

    target_json = json_output or data_path.with_suffix(".benchmark.json")
    target_md = md_output or target_json.with_suffix(".md")
    target_json.parent.mkdir(parents=True, exist_ok=True)
    target_md.parent.mkdir(parents=True, exist_ok=True)
    target_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    target_md.write_text(_build_markdown(report) + "\n", encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run benchmark/eval scoring for a research dataset")
    parser.add_argument("--data", required=True, help="Dataset CSV path")
    parser.add_argument("--registry", required=True, help="Source registry CSV path")
    parser.add_argument("--output-json", required=True, help="JSON report output path")
    parser.add_argument("--output-md", default="", help="Optional Markdown report output path")
    parser.add_argument("--variable", default="", help="Optional registry variable filter")
    parser.add_argument("--value-col", default="", help="Comma-separated value columns to score")
    parser.add_argument("--key", default="province,year", help="Comma-separated key columns")
    parser.add_argument("--year-start", type=int, default=None, help="Optional expected year range start")
    parser.add_argument("--year-end", type=int, default=None, help="Optional expected year range end")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_benchmark_eval(
        data_path=Path(args.data).resolve(),
        registry_path=Path(args.registry).resolve(),
        variable=(args.variable or "").strip(),
        value_cols=parse_csv_list(args.value_col),
        key_cols=parse_csv_list(args.key),
        year_start=args.year_start,
        year_end=args.year_end,
        json_output=Path(args.output_json).resolve(),
        md_output=Path(args.output_md).resolve() if args.output_md else None,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
