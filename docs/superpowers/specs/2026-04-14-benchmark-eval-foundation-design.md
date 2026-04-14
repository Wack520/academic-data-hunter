# Benchmark / Eval Foundation Design

## Summary

The next milestone should add a **benchmark/eval layer** that scores a research-data run on reliability, not just raw completion. The first version should evaluate a dataset plus source registry and produce machine-readable plus human-readable reports.

## Goal

Measure whether a run is good enough for serious research use by answering:

- how much of the target panel is filled
- whether filled rows have complete provenance
- whether dataset rows match the source registry
- whether C-level sources are cross-checked
- what the source-quality mix looks like

## Scope

### Inputs

- dataset CSV
- source registry CSV
- value columns
- optional variable filter
- optional year range for expected panel coverage

### Outputs

- JSON report
- Markdown summary
- overall score and component metrics

## Metrics

### Coverage

- expected key count
- filled key count
- fill rate

### Provenance quality

- provenance completeness rate
- registry match rate
- C-level cross-check rate
- source-level distribution
- weighted source quality score

### Composite score

The first version should provide a simple 0-100 score to make runs comparable. It does not need to be academically perfect yet; it needs to be stable, inspectable, and useful.

## Strategic value

This moves the project from “workflow scripts” toward “research-agent reliability infrastructure”. It also creates the foundation for:

- public benchmark cases
- agent-vs-agent comparisons
- future leaderboard/demo content

## Non-goals

- no public leaderboard yet
- no cloud benchmark service
- no LLM-based grading in this first version

## Deliverables

- `scripts/run_benchmark_eval.py`
- tests for score and output behavior
- docs for benchmark/eval usage
- optional Agent Hub integration
