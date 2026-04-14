# Auditable Research Agent Repositioning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reposition the project as provenance-first research-agent infrastructure and ship an evidence-pack export path that demonstrates the new product category.

**Architecture:** Keep the existing workflow/QC core, add a new evidence-pack export surface as a first-class artifact, and update documentation plus Agent Hub entry points so the new positioning is visible and executable.

**Tech Stack:** Python 3.11, argparse, csv/json/pathlib, FastAPI/legacy HTTP hub, pytest

---

### Task 1: Rewrite the public story

**Files:**
- Modify: `README.md`
- Create: `docs/positioning.md`
- Create: `docs/use-cases.md`
- Create: `docs/evidence-pack.md`
- Create: `docs/roadmap.md`

- [ ] **Step 1: Replace the README hero and framing**

Add a top section that leads with auditable research-agent positioning, a short value proposition, and a concrete output story: task spec → dataset → source registry → evidence pack.

- [ ] **Step 2: Add differentiation sections**

Document why the project is not a generic agent framework and why provenance, QC, and reproducibility matter for research workflows.

- [ ] **Step 3: Add supporting product docs**

Write dedicated docs for positioning, target use cases, evidence-pack semantics, and the next-step roadmap so the README can stay focused.

### Task 2: Add evidence-pack export

**Files:**
- Create: `scripts/export_evidence_pack.py`
- Create: `templates/evidence-pack-manifest.example.json`
- Test: `tests/test_export_evidence_pack.py`

- [ ] **Step 1: Define the export contract**

Support inputs for dataset CSV, registry CSV, output directory, optional variable filter, and optional value columns. Output:

```text
output/
  manifest.json
  dataset.csv
  source_registry.csv
  evidence_records.jsonl
  README.md
```

- [ ] **Step 2: Build row-level evidence records**

For each data row with values, attach provenance fields from the row plus matched registry metadata (prefer `source_id`, fallback to source tuple matching).

- [ ] **Step 3: Add summary generation**

Write a manifest with counts, variables, source levels, and generation timestamp, plus a markdown summary for quick human review.

- [ ] **Step 4: Add tests**

Cover successful export, source matching fallback behavior, and manifest/records output shape.

### Task 3: Expose evidence-pack export in the hub

**Files:**
- Modify: `scripts/agent_hub.py`
- Modify: `scripts/agent_hub_fastapi.py`
- Test: `tests/test_agent_hub_api.py`
- Test: `tests/test_agent_hub_fastapi_api.py`
- Test: `tests/test_agent_hub_cli.py`

- [ ] **Step 1: Add a new route**

Expose `/export-evidence-pack` in both legacy and FastAPI hubs, forwarding only safe arguments.

- [ ] **Step 2: Add chat command**

Support `export_evidence_pack --data ... --registry ... --output-dir ...` in REPL mode.

- [ ] **Step 3: Update endpoint/help text tests**

Extend route/CLI tests so the new command is part of the stable public surface.

### Task 4: Verify and document the milestone

**Files:**
- Modify: `README.md`
- Modify: `docs/architecture.md`

- [ ] **Step 1: Add example commands to docs**

Document a concrete exporter invocation and where the output bundle lands.

- [ ] **Step 2: Run focused verification**

Run:

```bash
python -m pytest -q tests/test_export_evidence_pack.py tests/test_agent_hub_api.py tests/test_agent_hub_fastapi_api.py tests/test_agent_hub_cli.py
python scripts/check_docs_command_paths.py --paths README.md docs
```

- [ ] **Step 3: Run broader repo verification**

Run:

```bash
python -m pytest -q
```

- [ ] **Step 4: Summarize follow-up work**

Capture the next attack-version items in the roadmap: benchmark/evals, MCP surface, and evidence inspector UI.
