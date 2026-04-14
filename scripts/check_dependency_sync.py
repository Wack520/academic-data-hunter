#!/usr/bin/env python3
"""
校验依赖声明是否同步：
1) pyproject.toml [project].dependencies
2) requirements.txt

用于 CI 快速防止依赖漂移。
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path


def _strip_inline_comment(line: str) -> str:
    cleaned = re.split(r"\s+#", line, maxsplit=1)[0]
    return cleaned.strip()


def load_requirements_txt(path: Path) -> list[str]:
    rows: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = _strip_inline_comment(raw)
        if not line or line.startswith("#"):
            continue
        rows.append(line)
    return rows


def load_pyproject_dependencies(path: Path) -> list[str]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    project = data.get("project")
    if not isinstance(project, dict):
        raise ValueError("pyproject.toml missing [project] table")
    dependencies = project.get("dependencies", [])
    if not isinstance(dependencies, list):
        raise ValueError("[project].dependencies must be a list")
    return [str(item).strip() for item in dependencies if str(item).strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Check pyproject dependencies are in sync with requirements.txt")
    parser.add_argument("--pyproject", default="pyproject.toml", help="Path to pyproject.toml")
    parser.add_argument("--requirements", default="requirements.txt", help="Path to requirements.txt")
    args = parser.parse_args()

    pyproject_path = Path(args.pyproject)
    requirements_path = Path(args.requirements)

    pyproject_deps = load_pyproject_dependencies(pyproject_path)
    requirements_deps = load_requirements_txt(requirements_path)

    pyproject_set = set(pyproject_deps)
    requirements_set = set(requirements_deps)

    only_in_pyproject = sorted(pyproject_set - requirements_set)
    only_in_requirements = sorted(requirements_set - pyproject_set)

    if not only_in_pyproject and not only_in_requirements:
        print("dependency sync check passed")
        return 0

    print("dependency sync check failed")
    if only_in_pyproject:
        print("Only in pyproject.toml [project].dependencies:")
        for item in only_in_pyproject:
            print(f"  - {item}")
    if only_in_requirements:
        print("Only in requirements.txt:")
        for item in only_in_requirements:
            print(f"  - {item}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
