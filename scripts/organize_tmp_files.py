#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把仓库根目录散落的临时文件（_tmp_* / tmp_*）归档到 tmp/legacy。
"""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="归档散落临时文件到 tmp/legacy")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--target", default="tmp/legacy")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    target = ROOT / args.target
    files = []
    for pat in ("_tmp_*", "tmp_*"):
        files.extend([p for p in ROOT.glob(pat) if p.is_file()])
    files = sorted({p.resolve() for p in files})

    if not files:
        print("[INFO] no scattered tmp files found")
        return

    print(f"[INFO] found={len(files)}")
    if args.dry_run:
        for f in files:
            print(f"  - {f.name}")
        return

    target.mkdir(parents=True, exist_ok=True)
    moved = 0
    for f in files:
        dst = target / f.name
        f.rename(dst)
        moved += 1
    print(f"[DONE] moved={moved} -> {target}")


if __name__ == "__main__":
    main()

