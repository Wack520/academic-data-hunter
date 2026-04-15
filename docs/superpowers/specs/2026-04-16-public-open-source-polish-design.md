# Public Open-Source Polish Design

**Date:** 2026-04-16  
**Scope:** GitHub-facing positioning, repository metadata, contributor entrypoints, and public launch readiness for `academic-data-hunter`

## Goal

Make the repository feel immediately credible to three audiences:

1. **Potential users** — understand in under 30 seconds what the repo does and why it matters.
2. **Recruiters / collaborators** — see strong product thinking, technical rigor, and polished OSS habits.
3. **Potential contributors** — know how to open issues, propose changes, and validate work locally.

## Non-goals

- No major new research-agent features.
- No architecture rewrite.
- No GitHub Pages site in this pass.
- No release engineering automation beyond existing CI.

## Recommended approach

Use a **public-facing polish pass** instead of feature expansion.

Why:
- It improves star-conversion fastest.
- It improves interview/demo value immediately.
- It reduces the "student side project" feel without delaying launch.

## Changes to make

### 1. Improve README first impression

Tighten the top of `README.md` so a GitHub visitor can quickly see:
- what the project is,
- why it is different,
- proof that it works,
- where to click next.

Planned changes:
- add CI badge,
- add a short "Why people star this" section,
- add a compact "Start here" link cluster,
- keep the existing benchmark proof but make it more scannable.

### 2. Add GitHub community surfaces

Add standard OSS files under `.github/` to increase professionalism and lower contributor friction:
- issue templates,
- pull request template.

These are high-signal for public repos and help the project look maintained.

### 3. Set repository metadata

Update GitHub repository metadata to match the new positioning:
- description,
- topics,
- visibility to public once checks pass.

### 4. Keep launch safe

Before changing visibility:
- verify CI still passes,
- verify README/doc command references still pass,
- verify working tree is clean,
- confirm no local-only runtime state is included.

## Success criteria

- Repo description is no longer empty.
- README gives a strong differentiating pitch in the first screen.
- Standard community files exist.
- Local verification passes.
- GitHub Actions passes on latest commit.
- Repository is switched from private to public.

## Risks

- Over-editing README may reduce clarity. Mitigation: preserve the provenance-first core message.
- Public launch before polish is verified could create a poor first impression. Mitigation: switch visibility only after green checks.
