from __future__ import annotations


def parse_csv_list(raw: str) -> list[str]:
    return [item.strip() for item in (raw or "").split(",") if item.strip()]


def has_value(row: dict[str, str], value_cols: list[str]) -> bool:
    if not value_cols:
        return True
    return any(bool((row.get(col) or "").strip()) for col in value_cols)


def registry_tuple_key(row: dict[str, str]) -> tuple[str, str, str]:
    return (
        (row.get("source_level") or "").strip(),
        (row.get("source_name") or "").strip(),
        (row.get("source_url") or "").strip(),
    )


def build_registry_indexes(
    rows: list[dict[str, str]],
) -> tuple[dict[str, dict[str, str]], dict[tuple[str, str, str], dict[str, str]]]:
    by_id: dict[str, dict[str, str]] = {}
    by_tuple: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in rows:
        source_id = (row.get("source_id") or "").strip()
        if source_id and source_id not in by_id:
            by_id[source_id] = row
        key = registry_tuple_key(row)
        if any(key) and key not in by_tuple:
            by_tuple[key] = row
    return by_id, by_tuple


def pick_registry_match(
    row: dict[str, str],
    registry_by_id: dict[str, dict[str, str]],
    registry_by_tuple: dict[tuple[str, str, str], dict[str, str]],
) -> tuple[str, dict[str, str] | None]:
    source_id = (row.get("source_id") or "").strip()
    if source_id and source_id in registry_by_id:
        return "source_id", registry_by_id[source_id]
    tuple_key = registry_tuple_key(row)
    if any(tuple_key) and tuple_key in registry_by_tuple:
        return "source_tuple", registry_by_tuple[tuple_key]
    return "unmatched", None


def build_resolved_provenance(
    row: dict[str, str],
    match_mode: str,
    registry_match: dict[str, str] | None,
) -> dict[str, object]:
    registry_record = registry_match or {}
    return {
        "match_mode": match_mode,
        "source_id": (row.get("source_id") or "").strip(),
        "source_level": (row.get("source_level") or "").strip(),
        "source_name": (row.get("source_name") or "").strip(),
        "source_url": (row.get("source_url") or "").strip(),
        "resolved_source_id": (row.get("source_id") or "").strip() or (registry_record.get("source_id") or "").strip(),
        "resolved_source_level": (row.get("source_level") or "").strip()
        or (registry_record.get("source_level") or "").strip(),
        "resolved_source_name": (row.get("source_name") or "").strip()
        or (registry_record.get("source_name") or "").strip(),
        "resolved_source_url": (row.get("source_url") or "").strip()
        or (registry_record.get("source_url") or "").strip(),
        "cross_check_url": (row.get("cross_check_url") or "").strip(),
        "access_date": (row.get("access_date") or "").strip(),
        "note": (row.get("note") or "").strip(),
        "registry_record": registry_record,
    }
