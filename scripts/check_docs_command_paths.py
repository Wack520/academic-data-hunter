#!/usr/bin/env python3
"""
校验文档中的 `python xxx.py` 命令脚本路径是否存在。

目标：
- 防止 README / docs / workflow 文档里的示例命令随重构漂移失效。
- 同时兼容两种常见写法：
  1) 相对仓库根目录（如 `python scripts/run_round.py`）
  2) 相对文档文件目录（如 `python ../../tools/qc_checker.py`）
"""

from __future__ import annotations

import argparse
import logging
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path

DEFAULT_SCAN_PATHS = ("README.md", "CONTRIBUTING.md", "docs", ".agent/workflows")
IGNORE_DIRS = {".git", ".venv", "__pycache__", ".mypy_cache", ".pytest_cache", ".ruff_cache", "tmp"}


@dataclass(frozen=True)
class CommandRefIssue:
    markdown_file: Path
    line_no: int
    script_ref: str
    checked_candidates: tuple[Path, ...]


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", force=True)


def _iter_markdown_files(root: Path, scan_paths: list[str]) -> list[Path]:
    files: list[Path] = []
    for raw in scan_paths:
        p = (root / raw).resolve()
        if p.is_file() and p.suffix.lower() == ".md":
            files.append(p)
            continue
        if p.is_dir():
            for md in p.rglob("*.md"):
                if any(part in IGNORE_DIRS for part in md.parts):
                    continue
                files.append(md.resolve())
    return sorted(dict.fromkeys(files))


def _extract_python_script_refs(text: str) -> list[tuple[int, str]]:
    refs: list[tuple[int, str]] = []
    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        try:
            tokens = shlex.split(line, posix=False)
        except ValueError:
            continue
        if not tokens:
            continue
        launcher = Path(tokens[0]).name.lower()
        if launcher not in {"python", "python3", "py"}:
            continue

        script_ref = ""
        for token in tokens[1:]:
            if token in {"-m", "-c"}:
                script_ref = ""
                break
            cleaned = token.strip().strip("\"'")
            if cleaned.startswith("-"):
                continue
            if cleaned.lower().endswith(".py"):
                script_ref = cleaned
                break
        if not script_ref:
            continue
        refs.append((line_no, script_ref))
    return refs


def _is_placeholder_ref(script_ref: str) -> bool:
    return any(marker in script_ref for marker in ("<", ">", "{", "}", "$"))


def _resolve_candidates(root: Path, markdown_file: Path, script_ref: str) -> tuple[Path, ...]:
    ref_path = Path(script_ref)
    if ref_path.is_absolute():
        return (ref_path,)
    return ((root / ref_path).resolve(), (markdown_file.parent / ref_path).resolve())


def check_docs_command_paths(root: Path, scan_paths: list[str]) -> list[CommandRefIssue]:
    issues: list[CommandRefIssue] = []
    markdown_files = _iter_markdown_files(root, scan_paths)
    for md in markdown_files:
        text = md.read_text(encoding="utf-8", errors="ignore")
        for line_no, script_ref in _extract_python_script_refs(text):
            if _is_placeholder_ref(script_ref):
                continue
            candidates = _resolve_candidates(root, md, script_ref)
            if any(candidate.exists() for candidate in candidates):
                continue
            issues.append(
                CommandRefIssue(
                    markdown_file=md,
                    line_no=line_no,
                    script_ref=script_ref,
                    checked_candidates=candidates,
                )
            )
    return issues


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="检查文档中的 python 脚本路径是否存在")
    parser.add_argument("--root", default=".", help="仓库根目录")
    parser.add_argument(
        "--paths",
        nargs="*",
        default=list(DEFAULT_SCAN_PATHS),
        help="要扫描的文件/目录（默认：README.md CONTRIBUTING.md docs .agent/workflows）",
    )
    return parser.parse_args()


def main() -> int:
    configure_logging()
    args = parse_args()
    root = Path(args.root).resolve()
    issues = check_docs_command_paths(root, list(args.paths))
    if not issues:
        logging.info("docs command path check passed (%s files/dirs)", len(args.paths))
        return 0

    logging.error("docs command path check failed: %s issue(s)", len(issues))
    for issue in issues:
        display_file = issue.markdown_file.relative_to(root)
        checked = " | ".join(str(p) for p in issue.checked_candidates)
        logging.error("  %s:%s -> %s", display_file, issue.line_no, issue.script_ref)
        logging.error("    checked: %s", checked)
    return 1


if __name__ == "__main__":
    sys.exit(main())
