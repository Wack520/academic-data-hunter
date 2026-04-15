# Public Open-Source Polish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `academic-data-hunter` more compelling as a public GitHub project for users, contributors, and recruiters.

**Architecture:** Keep the technical core unchanged and improve the repository's public-facing surfaces: README entrypoint, GitHub community files, and repository metadata. Finish with local and GitHub verification before switching the repository to public.

**Tech Stack:** Markdown, GitHub repository settings, existing Python verification scripts, GitHub Actions.

---

### Task 1: README public-facing polish

**Files:**
- Modify: `README.md`

- [ ] Add a CI badge near the top so visitors immediately see current project health.
- [ ] Add a short "Start here" block with links to the highest-signal docs.
- [ ] Add a brief section that explains why the repo is star-worthy / differentiated.
- [ ] Keep the benchmark proof section visible and scannable.

### Task 2: Contributor-facing GitHub files

**Files:**
- Create: `.github/ISSUE_TEMPLATE/bug_report.yml`
- Create: `.github/ISSUE_TEMPLATE/feature_request.yml`
- Create: `.github/ISSUE_TEMPLATE/config.yml`
- Create: `.github/pull_request_template.md`

- [ ] Add a structured bug report template.
- [ ] Add a structured feature request template.
- [ ] Add issue template config for discoverability.
- [ ] Add a pull request template aligned with this repo's verification workflow.

### Task 3: Repository metadata and launch state

**Files:**
- Modify: GitHub repository settings for `Wack520/academic-data-hunter`

- [ ] Set a concise repository description.
- [ ] Add relevant repository topics.
- [ ] Switch visibility from private to public after verification passes.

### Task 4: Verification

**Files:**
- Verify: `README.md`, `.github/**`, existing CI workflow

- [ ] Run `python scripts/check_docs_command_paths.py --paths README.md docs .github`.
- [ ] Run `python -m ruff check .`.
- [ ] Run `python -m pytest -q`.
- [ ] Commit the polish changes with a clear message.
- [ ] Push and wait for GitHub Actions to turn green.
