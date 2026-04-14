# Showcase

This page is the fastest way to understand what `academic-data-hunter` already proves.

## 1. It produces reviewable delivery artifacts

The project does not stop at “the agent found some data”.

A typical run can now output:

```text
task spec
  -> next-round task
  -> dataset.csv
  -> source_registry.csv
  -> evidence_records.jsonl
  -> benchmark report
```

That makes it usable for:

- academic competition teams
- research assistants
- policy / consulting research
- developers building research agents that need a trustworthy data layer

## 2. It already scores real runs

Real Case01 benchmark result generated from:

```bash
python scripts/run_benchmark_eval.py ^
  --data cases/case01-nev-carbon/data/charging_piles_by_province.csv ^
  --registry cases/case01-nev-carbon/data/source_registry.csv ^
  --variable charging ^
  --value-col public_charging_piles ^
  --year-start 2017 ^
  --year-end 2023 ^
  --output-json tmp/benchmark/case01-charging.json ^
  --output-md tmp/benchmark/case01-charging.md
```

Observed metrics:

| Metric | Value |
|---|---:|
| fill rate | 40.95 |
| provenance completeness | 100.00 |
| registry match rate | 100.00 |
| C-level cross-check rate | 100.00 |
| source quality score | 59.53 |
| overall score | 73.26 |

## 3. It already ships evidence-backed outputs

Example evidence-pack layout:

```text
tmp/evidence-pack/case01-charging/
  manifest.json
  dataset.csv
  source_registry.csv
  evidence_records.jsonl
  README.md
```

This is a much stronger public demo than a chat transcript.

## 4. It is already integration-ready

Current integration surfaces:

- **CLI** scripts
- **Agent Hub API**
- **local stdio MCP server**

MCP tools exposed today:

- `run_round`
- `validate_round`
- `export_evidence_pack`
- `benchmark_eval`

## 5. Why this is star-worthy

This repo is interesting because it sits at the intersection of:

- agent systems
- data engineering
- provenance / reliability
- real-world research workflows

Instead of competing with generic agent frameworks on orchestration alone, it focuses on the layer that most demos ignore:

> **turning agent work into auditable, reviewable, reproducible research assets**
