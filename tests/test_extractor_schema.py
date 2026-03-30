from __future__ import annotations

import json
from pathlib import Path

from tools.candidate_extractor import extract_candidates
from tools.extractor_schema import load_extractor_schema


def test_custom_schema_supports_non_nev_field(tmp_path: Path) -> None:
    schema_path = tmp_path / "population-schema.json"
    schema_path.write_text(
        json.dumps(
            {
                "required_term": "常住人口",
                "any_terms": ["常住人口"],
                "exclude_phrases": [],
                "value_tokens": ["年末常住人口", "常住人口"],
                "fallback_pattern": r"(?:年末常住人口|常住人口)[^。；，,]{0,20}([0-9]+(?:\\.[0-9]+)?)\\s*({units})",
                "unit_to_10k": {"万人": 1.0, "人": 0.0001},
                "search_positive_terms": {"常住人口": 4},
                "search_negative_terms": {"全国": -4},
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    schema = load_extractor_schema(schema_path)
    text = "截至2024年末，湖北省常住人口为5800万人。"
    results = extract_candidates("湖北省", "https://www.hubei.gov.cn/data", text, year=2024, schema=schema)

    assert len(results) == 1
    assert results[0]["unit"] == "万人"
    assert results[0]["value_10k"] == 5800.0
