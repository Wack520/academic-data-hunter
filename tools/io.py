"""
通用 I/O 工具 — CSV 读写、文件操作
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import TypeAlias

Row: TypeAlias = dict[str, str]


def load_csv(path: str | Path) -> list[Row]:
    """读取 CSV 文件，返回字典列表。自动处理 BOM (utf-8-sig)。"""
    with open(path, encoding="utf-8-sig") as f:
        return [dict(row) for row in csv.DictReader(f)]


def save_csv(rows: list[Row], path: str | Path, fieldnames: list[str] | None = None) -> None:
    """写入 CSV 文件。fieldnames 默认取第一行的 keys。"""
    if not rows:
        return
    if fieldnames is None:
        fieldnames = list(rows[0].keys())
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
