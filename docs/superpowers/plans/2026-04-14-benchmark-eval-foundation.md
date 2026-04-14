# Benchmark / Eval Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a benchmark/eval layer that scores research-data runs on coverage and provenance quality, producing JSON and Markdown reports.

**Architecture:** Implement a standalone benchmark-eval script with deterministic scoring, reuse provenance matching logic used by evidence-pack export, and expose the report through docs and Agent Hub.

**Tech Stack:** Python 3.11, argparse, csv/json/pathlib, pytest

---

### Task 1: Define eval behavior with tests

**Files:**
- Create: `tests/test_benchmark_eval.py`
- Modify: `tests/test_agent_hub_api.py`
- Modify: `tests/test_agent_hub_fastapi_api.py`
- Modify: `tests/test_agent_hub_cli.py`

- [ ] **Step 1: Add direct benchmark-eval tests**
- [ ] **Step 2: Verify expected report structure and core metrics**
- [ ] **Step 3: Add Agent Hub route/CLI expectations if integrated**

### Task 2: Implement benchmark-eval script

**Files:**
- Create: `scripts/run_benchmark_eval.py`
- Create or modify shared provenance helpers as needed

- [ ] **Step 1: Parse inputs and load rows**
- [ ] **Step 2: Compute coverage and provenance metrics**
- [ ] **Step 3: Compute overall score and write JSON/Markdown outputs**

### Task 3: Document the eval layer

**Files:**
- Create: `docs/benchmark-evals.md`
- Modify: `README.md`
- Modify: `docs/roadmap.md`

- [ ] **Step 1: Add usage docs and rationale**
- [ ] **Step 2: Add benchmark/eval command examples**

### Task 4: Verify

**Files:**
- None

- [ ] **Step 1: Run focused tests**
- [ ] **Step 2: Run lint/docs verification**
- [ ] **Step 3: Run full pytest**
