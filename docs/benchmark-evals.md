# Benchmark / Eval Foundation

This project now includes a first benchmark/eval layer for research-data runs.

## What it measures

The current evaluator scores a run on:

- **fill rate** — how much of the target panel is covered
- **provenance completeness** — whether filled rows carry enough source context
- **registry match rate** — whether dataset rows can be reconciled with the source registry
- **C-level cross-check rate** — whether weaker sources were cross-checked
- **source quality score** — weighted mix of A/B/C-level sources

These roll up into a deterministic **overall score (0-100)**.

## Why this matters

Agent demos often stop at “I found the data”. Real research workflows need to answer:

- How complete is this run?
- How trustworthy are these rows?
- Can a reviewer inspect the provenance?
- Is this good enough to continue into modeling or writing?

This benchmark/eval layer is the first step toward public reliability benchmarks for research agents.

## Usage

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

## Outputs

- `*.json` — machine-readable metrics and counts
- `*.md` — human-readable summary for review

## Current scoring model

The first version uses stable heuristic weights:

- fill rate: 35%
- provenance completeness: 20%
- registry match rate: 20%
- source quality score: 15%
- C-level cross-check rate: 10%

This is intentionally simple for now. Later versions can add:

- benchmark specs
- task families
- agent-vs-agent comparisons
- public leaderboard/demo reports
