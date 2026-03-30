"""
Case01 一键QC脚本（充电桩 + 全国公交年表）。

示例：
python cases/case01-nev-carbon/scripts/qc_case01.py
python cases/case01-nev-carbon/scripts/qc_case01.py --no-strict-c-cross-check
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run_step(name: str, cmd: list[str], cwd: str) -> bool:
    print(f"\n=== {name} ===")
    print("命令:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode == 0:
        print(f"[通过] {name}")
        return True
    print(f"[失败] {name} (exit={result.returncode})")
    return False


def main():
    parser = argparse.ArgumentParser(description="Case01 一键QC")
    parser.add_argument(
        "--no-strict-c-cross-check",
        action="store_true",
        help="关闭 C级 cross_check_url 严格校验",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[3]
    py = sys.executable
    strict = not args.no_strict_c_cross_check

    charging = "cases/case01-nev-carbon/data/charging_piles_by_province.csv"
    national = "cases/case01-nev-carbon/data/national_ev_bus_annual.csv"
    registry = "cases/case01-nev-carbon/data/source_registry.csv"

    steps = [
        (
            "QC-充电桩基础检查",
            [
                py,
                "tools/qc_checker.py",
                charging,
                "--required",
                "source_url,source_id,access_date",
                "--value-col",
                "public_charging_piles",
                "--check-unit",
                "台",
            ],
        ),
        (
            "QC-充电桩来源一致性",
            [
                py,
                "scripts/validate_round.py",
                "--data",
                charging,
                "--registry",
                registry,
                "--variable",
                "charging",
                "--value-col",
                "public_charging_piles",
                "--check-unit",
                "台",
            ]
            + (["--strict-c-cross-check"] if strict else []),
        ),
        (
            "QC-全国公交年表基础检查",
            [
                py,
                "tools/qc_checker.py",
                national,
                "--key",
                "year",
                "--required",
                "source_url,source_id,access_date",
                "--value-col",
                "national_nev_buses,national_bev_buses",
                "--check-unit",
                "辆",
            ],
        ),
        (
            "QC-全国公交年表来源一致性",
            [
                py,
                "scripts/validate_round.py",
                "--data",
                national,
                "--registry",
                registry,
                "--variable",
                "nev_buses",
                "--key",
                "year",
                "--value-col",
                "national_nev_buses,national_bev_buses",
                "--check-unit",
                "辆",
            ]
            + (["--strict-c-cross-check"] if strict else []),
        ),
    ]

    ok = True
    for name, cmd in steps:
        if not run_step(name, cmd, str(root)):
            ok = False

    print("\n=== 总结 ===")
    if ok:
        print("Case01 全部QC通过。")
        return
    print("Case01 存在未通过项，请根据失败步骤修复。")
    sys.exit(1)


if __name__ == "__main__":
    main()
