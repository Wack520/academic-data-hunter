#!/usr/bin/env python3
"""
Run a reproducible local review gate and persist machine/human-readable records.

Default outputs:
  - tmp/review/review-gate-latest.json
  - tmp/review/review-gate-latest.md
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class CheckResult:
    name: str
    command: list[str]
    returncode: int
    duration_sec: float
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def run_check(name: str, command: list[str], cwd: Path) -> CheckResult:
    started = time.perf_counter()
    proc = subprocess.run(command, cwd=cwd, capture_output=True, text=True)
    duration = time.perf_counter() - started
    return CheckResult(
        name=name,
        command=command,
        returncode=proc.returncode,
        duration_sec=round(duration, 3),
        stdout=proc.stdout,
        stderr=proc.stderr,
    )


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def trim_block(text: str, limit: int = 4000) -> str:
    value = (text or "").strip()
    if len(value) <= limit:
        return value
    return value[: limit - 20] + "\n...[truncated]..."


def build_markdown(results: list[CheckResult], generated_at: str, python_exe: str) -> str:
    lines: list[str] = []
    lines.append("# Review Gate Report")
    lines.append("")
    lines.append(f"- Generated at (UTC): {generated_at}")
    lines.append(f"- Python executable: `{python_exe}`")
    lines.append("")
    lines.append("| Check | Status | Duration(s) |")
    lines.append("|---|---:|---:|")
    for item in results:
        lines.append(f"| {item.name} | {'✅' if item.ok else '❌'} | {item.duration_sec:.3f} |")

    for item in results:
        lines.append("")
        lines.append(f"## {item.name}")
        lines.append("")
        lines.append("```bash")
        lines.append(" ".join(item.command))
        lines.append("```")
        lines.append("")
        lines.append(f"- Return code: `{item.returncode}`")
        lines.append("")
        if item.stdout.strip():
            lines.append("<details><summary>stdout</summary>")
            lines.append("")
            lines.append("```text")
            lines.append(trim_block(item.stdout))
            lines.append("```")
            lines.append("")
            lines.append("</details>")
        if item.stderr.strip():
            lines.append("<details><summary>stderr</summary>")
            lines.append("")
            lines.append("```text")
            lines.append(trim_block(item.stderr))
            lines.append("```")
            lines.append("")
            lines.append("</details>")

    lines.append("")
    overall_ok = all(item.ok for item in results)
    lines.append(f"## Overall: {'PASS ✅' if overall_ok else 'FAIL ❌'}")
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run review gate checks and persist report artifacts")
    parser.add_argument("--cwd", default=".", help="Repository root")
    parser.add_argument("--coverage-threshold", type=int, default=80, help="coverage report fail-under threshold")
    parser.add_argument("--json-output", default="tmp/review/review-gate-latest.json")
    parser.add_argument("--md-output", default="tmp/review/review-gate-latest.md")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.cwd).resolve()
    py = str(Path(sys.executable))

    checks: list[tuple[str, list[str]]] = [
        ("dependency_sync", [py, "scripts/check_dependency_sync.py"]),
        ("docs_command_paths", [py, "scripts/check_docs_command_paths.py", "--paths", "."]),
        ("ruff_check", [py, "-m", "ruff", "check", "."]),
        ("ruff_format_check", [py, "-m", "ruff", "format", "--check", "."]),
        ("mypy_tools", [py, "-m", "mypy", "tools/", "--ignore-missing-imports"]),
        ("compileall", [py, "-m", "compileall", "-q", "scripts", "tools", "tests", "cases"]),
        ("pytest", [py, "-m", "pytest", "-q", "tests/"]),
        ("coverage_run", [py, "-m", "coverage", "run", "-m", "pytest", "-q", "tests/"]),
        ("coverage_report", [py, "-m", "coverage", "report", f"--fail-under={args.coverage_threshold}"]),
    ]

    results: list[CheckResult] = []
    for name, command in checks:
        result = run_check(name, command, cwd=root)
        results.append(result)
        if result.returncode != 0 and name in {"pytest", "coverage_run", "coverage_report"}:
            # Keep going to persist artifacts for diagnosis but do not short-circuit.
            pass

    generated_at = datetime.now(UTC).isoformat()
    payload = {
        "generated_at_utc": generated_at,
        "python_executable": py,
        "cwd": str(root),
        "overall_ok": all(item.ok for item in results),
        "checks": [
            {
                **asdict(item),
                "ok": item.ok,
            }
            for item in results
        ],
    }

    json_path = (root / args.json_output).resolve()
    md_path = (root / args.md_output).resolve()
    write_json(json_path, payload)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(build_markdown(results, generated_at=generated_at, python_exe=py), encoding="utf-8")

    print(f"json={json_path}")
    print(f"md={md_path}")
    return 0 if payload["overall_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
