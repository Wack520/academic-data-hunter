from __future__ import annotations

import csv
import json
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def test_run_auto_rounds_end_to_end_with_mock_agent(tmp_path: Path) -> None:
    data_path = tmp_path / "panel.csv"
    task_path = tmp_path / "next-round-task.md"
    report_path = tmp_path / "auto-round-report.md"
    agent_state_path = tmp_path / "agent_state.json"
    validate_state_path = tmp_path / "validate_state.json"
    agent_script_path = tmp_path / "mock_agent.py"
    validate_script_path = tmp_path / "mock_validate.py"

    _write_csv(
        data_path,
        [
            {"province": "北京", "year": "2023", "target_value": "100"},
            {"province": "天津", "year": "2023", "target_value": ""},
        ],
    )

    agent_script_path.write_text(
        textwrap.dedent(
            """
            from __future__ import annotations

            import argparse
            import csv
            import json
            from pathlib import Path


            def main() -> int:
                parser = argparse.ArgumentParser()
                parser.add_argument("--data", required=True)
                parser.add_argument("--task", required=True)
                parser.add_argument("--round", required=True)
                parser.add_argument("--state", required=True)
                args = parser.parse_args()

                state_path = Path(args.state)
                state = {"calls": 0, "updates": 0, "task_exists": []}
                if state_path.exists():
                    state = json.loads(state_path.read_text(encoding="utf-8"))
                state["calls"] = int(state.get("calls", 0)) + 1
                state["task_exists"].append(Path(args.task).exists())

                updated = False
                if state["calls"] == 1:
                    data_path = Path(args.data)
                    with data_path.open("r", encoding="utf-8-sig", newline="") as f:
                        rows = list(csv.DictReader(f))
                        fieldnames = rows[0].keys()
                    for row in rows:
                        if not (row.get("target_value") or "").strip():
                            row["target_value"] = "200"
                            updated = True
                            break
                    if updated:
                        with data_path.open("w", encoding="utf-8-sig", newline="") as f:
                            writer = csv.DictWriter(f, fieldnames=fieldnames)
                            writer.writeheader()
                            writer.writerows(rows)

                if updated:
                    state["updates"] = int(state.get("updates", 0)) + 1
                state_path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
                return 0


            if __name__ == "__main__":
                raise SystemExit(main())
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    validate_script_path.write_text(
        textwrap.dedent(
            """
            from __future__ import annotations

            import argparse
            import json
            from pathlib import Path


            def main() -> int:
                parser = argparse.ArgumentParser()
                parser.add_argument("--data", required=True)
                parser.add_argument("--task", required=True)
                parser.add_argument("--round", required=True)
                parser.add_argument("--state", required=True)
                args = parser.parse_args()

                if not Path(args.data).exists() or not Path(args.task).exists():
                    return 2

                state_path = Path(args.state)
                state = {"calls": 0}
                if state_path.exists():
                    state = json.loads(state_path.read_text(encoding="utf-8"))
                state["calls"] = int(state.get("calls", 0)) + 1
                state_path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
                return 0


            if __name__ == "__main__":
                raise SystemExit(main())
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    py_exec = Path(sys.executable).as_posix()
    agent_cmd = (
        f"\"{py_exec}\" \"{agent_script_path.as_posix()}\" "
        f"--data \"{{data}}\" --task \"{{task_file}}\" --round \"{{round}}\" "
        f"--state \"{agent_state_path.as_posix()}\""
    )
    validate_cmd = (
        f"\"{py_exec}\" \"{validate_script_path.as_posix()}\" "
        f"--data \"{{data}}\" --task \"{{task_file}}\" --round \"{{round}}\" "
        f"--state \"{validate_state_path.as_posix()}\""
    )

    run_cmd = [
        sys.executable,
        "scripts/run_auto_rounds.py",
        "--data",
        str(data_path),
        "--value-col",
        "target_value",
        "--year-start",
        "2023",
        "--year-end",
        "2023",
        "--top-years",
        "1",
        "--task-output",
        str(task_path),
        "--max-rounds",
        "3",
        "--min-gain",
        "1",
        "--patience",
        "1",
        "--agent-cmd",
        agent_cmd,
        "--validate-cmd",
        validate_cmd,
        "--report",
        str(report_path),
    ]
    result = subprocess.run(run_cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0, f"stdout={result.stdout}\nstderr={result.stderr}"

    assert task_path.exists()
    assert report_path.exists()

    report = report_path.read_text(encoding="utf-8")
    assert "## Round 1" in report
    assert "## Round 2" in report
    assert "连续低增益达到 1 轮，提前停止。" in report

    rows = _read_csv(data_path)
    assert rows[1]["target_value"] == "200"

    agent_state = json.loads(agent_state_path.read_text(encoding="utf-8"))
    assert agent_state["calls"] == 2
    assert agent_state["updates"] == 1
    assert agent_state["task_exists"] == [True, True]

    validate_state = json.loads(validate_state_path.read_text(encoding="utf-8"))
    assert validate_state["calls"] == 2
