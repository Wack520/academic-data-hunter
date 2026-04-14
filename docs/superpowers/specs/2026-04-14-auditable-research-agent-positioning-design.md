# Auditable Research Agent Repositioning Design

## Summary

`academic-data-hunter` should stop presenting itself as a generic AI agent toolkit and instead become **provenance-first infrastructure for research data agents**. The core promise is not “search with AI”, but **turn research tasks into auditable datasets, evidence packs, and reproducible delivery artifacts**.

## Why this direction

- Generic agent orchestration is rapidly commoditizing.
- The repository already has stronger primitives in provenance, QC, workflow control, and case-based delivery than in model/runtime novelty.
- Real users in research, academic competitions, policy analysis, and data-heavy writing care about **traceability, source grading, and reproducibility** more than chat UX.

## Product positioning

### One-line positioning

> Provenance-first infrastructure for auditable research data agents.

### Core user promise

Given a research spec and a data gap, the project should help users:

1. Generate the next collection task.
2. Collect or review candidate data.
3. Validate source completeness and source quality.
4. Export a reproducible evidence-backed delivery bundle.

## Strategic decisions

### 1. Keep the repository name, change the category

Keep `academic-data-hunter`, but shift the public category from:

- “学术竞赛数据搜集工具包”

to:

- “高可信研究数据 Agent 基础设施”
- “auditable dataset workflow for research agents”

### 2. Ship a concrete “evidence pack” artifact

The first aggressive milestone should add a concrete deliverable beyond CSV files:

- merged dataset copy
- source registry copy
- manifest JSON
- row-level records JSONL with provenance fields
- markdown summary

This becomes the easiest demo artifact for README, demos, and job-search storytelling.

### 3. Make the evidence layer callable

The evidence-pack export should be available from:

- a standalone script
- the hybrid Agent Hub API
- the hybrid Agent Hub chat mode

This keeps the project usable as a component inside broader agent stacks.

### 4. Add product-facing docs

The repository needs docs that explain:

- who the project is for
- why provenance matters
- what an evidence pack is
- how the roadmap evolves toward MCP and benchmark layers

## Non-goals for this milestone

- No generic chat UI.
- No attempt to become a full general-purpose agent platform.
- No large MCP server implementation yet.
- No cloud SaaS or heavy deployment work.

## First milestone scope

### Documentation

- Rewrite `README.md` around the new positioning.
- Add:
  - `docs/positioning.md`
  - `docs/use-cases.md`
  - `docs/evidence-pack.md`
  - `docs/roadmap.md`

### Product capability

- Add `scripts/export_evidence_pack.py`.
- Add a template manifest or schema under `templates/`.
- Add tests for the exporter.

### Integration

- Expose evidence-pack export through `scripts/agent_hub.py`.
- Mirror it in `scripts/agent_hub_fastapi.py`.
- Add tests for both API layers and chat mode.

## Success criteria

- A new visitor can understand the project in under 15 seconds.
- The README clearly differentiates the project from generic agent frameworks.
- A user can run one command and get an evidence-backed delivery bundle.
- The new exporter and hub integrations are covered by tests and pass repo verification.

## Longer-term roadmap after this milestone

1. Public benchmark/eval suite for research-agent reliability.
2. MCP-compatible tool surface.
3. Lightweight evidence inspector UI.
4. More public case studies and polished demo assets.
