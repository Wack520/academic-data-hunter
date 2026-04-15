# README Banner and First Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve first-visit conversion for `academic-data-hunter` with a stronger banner, stronger README hero, and a first public launch release draft.

**Architecture:** Keep the technical product unchanged and enhance public-facing surfaces only. Use repo-native assets and markdown so the improvements remain easy to maintain.

**Tech Stack:** Markdown, SVG/PNG assets, GitHub Releases, existing Python verification scripts.

---

### Task 1: Create banner/social preview assets

**Files:**
- Create: `docs/assets/github-social-preview.svg`
- Create: `docs/assets/github-social-preview.png`

- [ ] Design a simple banner with the project's key promise and proof-oriented keywords.
- [ ] Export a PNG version suitable for reuse in README and future GitHub/social contexts.

### Task 2: Polish README hero section

**Files:**
- Modify: `README.md`

- [ ] Insert the banner near the top.
- [ ] Add a more explicit one-sentence value proposition for users landing from GitHub.
- [ ] Add direct links for proof, use cases, roadmap, and contributing.

### Task 3: Add first release notes

**Files:**
- Create: `docs/releases/v0.1.0-public-launch.md`

- [ ] Write a first public launch note with highlights, what's included, proof, and next steps.
- [ ] Create a draft GitHub release for `v0.1.0` using the release note file.

### Task 4: Verify and publish changes

**Files:**
- Verify: `README.md`, `docs/assets/*`, `docs/releases/*`

- [ ] Run `python scripts/check_docs_command_paths.py --paths README.md docs .github`.
- [ ] Run `python -m ruff check .`.
- [ ] Run `python -m pytest -q`.
- [ ] Commit and push the changes.
- [ ] Confirm the draft release exists.
