# Chinese-First README Repositioning Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the repository landing experience shorter, clearer, and Chinese-first.

**Architecture:** Keep project functionality unchanged and only refactor the public-facing README and repo description. Replace broad/negative framing with direct positioning and reduce landing-page length.

**Tech Stack:** Markdown, GitHub repo metadata, existing verification scripts.

---

### Task 1: Rewrite README structure

**Files:**
- Modify: `README.md`

- [ ] Remove the banner image and banner-led hero section.
- [ ] Replace the top positioning with a concise Chinese one-sentence definition.
- [ ] Keep only short sections for capabilities, use cases, quick start, cases, docs, and contribution.
- [ ] Remove or collapse long advanced command sections from the landing page.

### Task 2: Update repository metadata

**Files:**
- Modify: GitHub repository settings for `Wack520/academic-data-hunter`

- [ ] Replace the English repo description with a concise Chinese description.

### Task 3: Verify and publish

**Files:**
- Verify: `README.md`

- [ ] Run `python scripts/check_docs_command_paths.py --paths README.md CONTRIBUTING.md docs .github`.
- [ ] Run `git status --short` to confirm the expected change set.
- [ ] Commit and push the README/metadata update.
