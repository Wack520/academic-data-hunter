#!/usr/bin/env python3
"""
Summarize current git workspace changes for review scoping.

Outputs a markdown report that helps split a noisy workspace into review batches.
"""

from __future__ import annotations

import argparse
import subprocess
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class StatusRow:
    raw_status: str
    path: str
    kind: str  # modified | added | deleted | renamed | untracked | other


def parse_status_porcelain(output: str) -> list[StatusRow]:
    rows: list[StatusRow] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        status = line[:2]
        raw_path = line[3:]
        if "->" in raw_path:
            raw_path = raw_path.split("->", 1)[1].strip()
        path = raw_path.strip().strip('"')
        if status == "??":
            kind = "untracked"
        elif "D" in status:
            kind = "deleted"
        elif "A" in status:
            kind = "added"
        elif "R" in status:
            kind = "renamed"
        elif "M" in status:
            kind = "modified"
        else:
            kind = "other"
        rows.append(StatusRow(raw_status=status, path=path, kind=kind))
    return rows


def top_level(path: str) -> str:
    p = Path(path)
    return p.parts[0] if p.parts else path


def build_report(rows: list[StatusRow]) -> str:
    by_kind = Counter(item.kind for item in rows)
    by_top = Counter(top_level(item.path) for item in rows)
    by_top_kind: dict[str, Counter[str]] = defaultdict(Counter)
    for item in rows:
        by_top_kind[top_level(item.path)][item.kind] += 1

    lines: list[str] = []
    lines.append("# Workspace Change Summary")
    lines.append("")
    lines.append(f"- Total changed paths: **{len(rows)}**")
    lines.append("")
    lines.append("## By status kind")
    lines.append("")
    for kind, count in sorted(by_kind.items(), key=lambda x: (-x[1], x[0])):
        lines.append(f"- {kind}: {count}")

    lines.append("")
    lines.append("## By top-level path")
    lines.append("")
    lines.append("| Top-level | Count | Breakdown |")
    lines.append("|---|---:|---|")
    for group, count in sorted(by_top.items(), key=lambda x: (-x[1], x[0])):
        breakdown = ", ".join(f"{k}:{v}" for k, v in sorted(by_top_kind[group].items()))
        lines.append(f"| {group} | {count} | {breakdown} |")

    lines.append("")
    lines.append("## Suggested review batches")
    lines.append("")
    lines.append(
        "1. **Infra & quality gates**: `.github/`, `pyproject.toml`, `requirements*.txt`, `scripts/check_*.py`, CI/docs checks"
    )
    lines.append("2. **Core runtime**: `scripts/agent_hub*.py`, `tools/*.py`")
    lines.append("3. **Tests**: `tests/`")
    lines.append("4. **Docs**: `README.md`, `docs/`, `.agent/workflows/`, `CONTRIBUTING.md`")
    lines.append("5. **Data/cases**: `cases/` (separate from code review)")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize git workspace changes")
    parser.add_argument("--cwd", default=".", help="Repository root")
    parser.add_argument("--output", default="tmp/review/workspace-change-summary.md")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.cwd).resolve()
    proc = subprocess.run(["git", "status", "--short"], cwd=root, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stderr)
        return proc.returncode

    rows = parse_status_porcelain(proc.stdout)
    report = build_report(rows)
    out = (root / args.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(f"output={out}")
    print(f"changed={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
