from __future__ import annotations

import subprocess

from scripts import agent_hub_common


def test_missing_required_fields_handles_absent_none_and_blank() -> None:
    missing = agent_hub_common.missing_required_fields(
        {"data": "x.csv", "value_col": " ", "year_start": None},
        ["data", "value_col", "year_start", "year_end"],
    )
    assert missing == ["value_col", "year_start", "year_end"]


def test_run_script_supports_script_name_and_relative_path() -> None:
    by_name = agent_hub_common.run_script("check_dependency_sync.py", ["--help"])
    assert by_name["returncode"] == 0
    assert by_name["ok"] is True
    assert "usage:" in by_name["stdout"].lower()

    by_rel_path = agent_hub_common.run_script("scripts/check_dependency_sync.py", ["--help"])
    assert by_rel_path["returncode"] == 0
    assert by_rel_path["ok"] is True
    assert "usage:" in by_rel_path["stdout"].lower()


def test_payload_to_args_and_args_list_to_payload_round_trip() -> None:
    payload = {
        "data": "cases/case01.csv",
        "year_start": 2017,
        "strict_c_cross_check": True,
        "disabled_flag": False,
        "optional_none": None,
    }
    args = agent_hub_common.payload_to_args(
        payload,
        ["data", "year_start", "strict_c_cross_check", "disabled_flag", "optional_none", "missing"],
    )
    assert args == ["--data", "cases/case01.csv", "--year-start", "2017", "--strict-c-cross-check"]

    rebuilt = agent_hub_common.args_list_to_payload(args)
    assert rebuilt == {
        "data": "cases/case01.csv",
        "year_start": "2017",
        "strict_c_cross_check": True,
    }


def test_args_list_to_payload_skips_non_flag_tokens() -> None:
    payload = agent_hub_common.args_list_to_payload(
        ["positional", "--foo", "bar", "--switch", "--num", "3", "tail-positional"]
    )
    assert payload == {"foo": "bar", "switch": True, "num": "3"}


def test_run_plan_then_auto_plan_failed(monkeypatch) -> None:
    calls: list[tuple[str, list[str]]] = []

    def fake_run_script(script_name: str, args: list[str]) -> dict:
        calls.append((script_name, args))
        return {
            "ok": False,
            "returncode": 2,
            "command": [script_name, *args],
            "stdout": "",
            "stderr": "plan error",
        }

    monkeypatch.setattr(agent_hub_common, "run_script", fake_run_script)
    result = agent_hub_common.run_plan_then_auto(
        {
            "spec_file": "templates/research-spec-template.json",
            "data": "cases/case01.csv",
            "value_col": "public_charging_piles",
            "year_start": 2017,
            "year_end": 2023,
            "agent_cmd": "echo injected",
            "validate_cmd": "echo injected",
        }
    )

    assert result["ok"] is False
    assert result["stage"] == "plan"
    assert result["error_code"] == "plan_failed"
    assert "plan error" in result["error"]
    assert result["auto_rounds"] is None
    assert calls == [("plan_research_workflow.py", ["--spec-file", "templates/research-spec-template.json"])]


def test_run_plan_then_auto_success_and_auto_failed(monkeypatch) -> None:
    calls: list[tuple[str, list[str]]] = []

    def fake_run_script(script_name: str, args: list[str]) -> dict:
        calls.append((script_name, args))
        if script_name == "plan_research_workflow.py":
            return {
                "ok": True,
                "returncode": 0,
                "command": [script_name, *args],
                "stdout": "plan-ok",
                "stderr": "",
            }
        return {
            "ok": False,
            "returncode": 1,
            "command": [script_name, *args],
            "stdout": "",
            "stderr": "auto-failed",
        }

    monkeypatch.setattr(agent_hub_common, "run_script", fake_run_script)
    result = agent_hub_common.run_plan_then_auto(
        {
            "spec_file": "templates/research-spec-template.json",
            "data": "cases/case01.csv",
            "value_col": "public_charging_piles",
            "year_start": 2017,
            "year_end": 2023,
            "agent_cmd": "echo injected",
            "validate_cmd": "echo injected",
        }
    )

    assert result["ok"] is False
    assert result["stage"] == "auto_rounds_failed"
    assert result["error_code"] == "auto_rounds_failed"
    assert "auto-failed" in result["error"]
    assert len(calls) == 2
    assert calls[0][0] == "plan_research_workflow.py"
    assert calls[1][0] == "run_auto_rounds.py"
    forwarded_auto_args = calls[1][1]
    assert "--agent-cmd" not in forwarded_auto_args
    assert "--validate-cmd" not in forwarded_auto_args


def test_run_plan_then_auto_input_validation_failed(monkeypatch) -> None:
    def fail_run_script(script_name: str, args: list[str]) -> dict:  # pragma: no cover - should not be called
        _ = (script_name, args)
        raise AssertionError("run_script should not be called when input validation fails")

    monkeypatch.setattr(agent_hub_common, "run_script", fail_run_script)
    result = agent_hub_common.run_plan_then_auto({"spec_file": "templates/research-spec-template.json"})
    assert result["ok"] is False
    assert result["stage"] == "input_validation"
    assert result["error_code"] == "missing_required_fields"
    assert "missing required fields" in result["error"]
    assert result["missing_fields"] == ["data", "value_col", "year_start", "year_end"]
    assert result["plan"] is None
    assert result["auto_rounds"] is None


def test_run_script_missing_file_returns_127() -> None:
    result = agent_hub_common.run_script("scripts/not_exists_script_foo.py", [])
    assert result["ok"] is False
    assert result["returncode"] == 127
    assert "script not found" in result["stderr"]


def test_run_script_timeout_returns_124(monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        _ = (args, kwargs)
        raise subprocess.TimeoutExpired(
            cmd=["python", "scripts/check_dependency_sync.py", "--help"],
            timeout=1,
            output="partial out",
            stderr="partial err",
        )

    monkeypatch.setattr(agent_hub_common.subprocess, "run", fake_run)
    result = agent_hub_common.run_script("check_dependency_sync.py", ["--help"])
    assert result["ok"] is False
    assert result["returncode"] == 124
    assert "partial out" in result["stdout"]
    assert "script timeout after" in result["stderr"]
