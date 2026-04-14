"""
通用 I/O 工具 — CSV 读写、文件操作
"""

from __future__ import annotations

import csv
import os
import tempfile
from pathlib import Path
from typing import TypeAlias

Row: TypeAlias = dict[str, str]


def load_csv(path: str | Path) -> list[Row]:
    """读取 CSV 文件，返回字典列表。自动处理 BOM (utf-8-sig)。"""
    with open(path, encoding="utf-8-sig") as f:
        return [dict(row) for row in csv.DictReader(f)]


def save_csv(rows: list[Row], path: str | Path, fieldnames: list[str] | None = None) -> None:
    """写入 CSV 文件（原子写入：先写临时文件再 rename，防崩溃损坏）。"""
    if not rows:
        return
    if fieldnames is None:
        fieldnames = list(rows[0].keys())
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=target.parent, suffix=".tmp", prefix=target.stem)
    try:
        with os.fdopen(fd, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(rows)
        Path(tmp_path).replace(target)
    except BaseException:
        Path(tmp_path).unlink(missing_ok=True)
        raise
