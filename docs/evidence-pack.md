# Evidence Pack

An evidence pack is the main delivery artifact for a research-agent run.

## Why it exists

CSV alone is not enough for serious research work. A reviewer needs:

- where the value came from
- how it was classified
- whether it was cross-checked
- whether the source registry matches the dataset rows

## Bundle contents

Current bundle layout:

```text
output/
  manifest.json
  dataset.csv
  source_registry.csv
  evidence_records.jsonl
  README.md
```

## Current exporter

```bash
python scripts/export_evidence_pack.py ^
  --data cases/case01-nev-carbon/data/charging_piles_by_province.csv ^
  --registry cases/case01-nev-carbon/data/source_registry.csv ^
  --variable charging ^
  --value-col public_charging_piles ^
  --output-dir tmp/evidence-pack/case01-charging
```

## Record semantics

Each `evidence_records.jsonl` line contains:

- dataset row key
- selected value columns
- row-level provenance fields
- matched registry record (if found)
- match mode (`source_id`, `source_tuple`, or `unmatched`)

## Intended evolution

Later versions can add:

- archived evidence snippets
- fetch metadata
- screenshot / page capture references
- dataset diff information between review rounds
