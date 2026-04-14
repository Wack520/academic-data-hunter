from __future__ import annotations

import os
import subprocess
import sys

from tools.config import AGENT_HUB_SCRIPT_TIMEOUT_SEC

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def missing_required_fields(payload: dict, required_keys: list[str]) -> list[str]:
    missing: list[str] = []
    for key in required_keys:
        if key not in payload:
            missing.append(key)
            continue
        value = payload.get(key)
        if value is None:
            missing.append(key)
            continue
        if isinstance(value, str) and not value.strip():
            missing.append(key)
    return missing


def run_script(script_name: str, args: list[str]) -> dict:
    """Run a project script as a subprocess and return structured result."""
    if "/" in script_name or os.path.sep in script_name:
        script_path = os.path.join(ROOT, script_name)
    else:
        script_path = os.path.join(ROOT, "scripts", script_name)
    if not os.path.exists(script_path):
        return {
            "ok": False,
            "returncode": 127,
            "command": [sys.executable, script_path, *args],
            "stdout": "",
            "stderr": f"script not found: {script_path}",
        }
    cmd = [sys.executable, script_path, *args]
    try:
        proc = subprocess.run(
            cmd,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=AGENT_HUB_SCRIPT_TIMEOUT_SEC,
        )
    except subprocess.TimeoutExpired as exc:
        stdout_text = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        stderr_text = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
        timeout_msg = f"script timeout after {AGENT_HUB_SCRIPT_TIMEOUT_SEC}s: {script_path}"
        stderr_full = f"{stderr_text}\n{timeout_msg}".strip()
        return {
            "ok": False,
            "returncode": 124,
            "command": cmd,
            "stdout": stdout_text,
            "stderr": stderr_full,
        }
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "command": cmd,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def payload_to_args(payload: dict, allow_keys: list[str]) -> list[str]:
    args: list[str] = []
    for key in allow_keys:
        if key not in payload:
            continue
        value = payload[key]
        flag = f"--{key.replace('_', '-')}"
        if isinstance(value, bool):
            if value:
                args.append(flag)
            continue
        if value is None:
            continue
        args.extend([flag, str(value)])
    return args


def args_list_to_payload(args: list[str]) -> dict:
    payload: dict = {}
    index = 0
    while index < len(args):
        token = args[index]
        if not token.startswith("--"):
            index += 1
            continue
        key = token[2:].replace("-", "_")
        # bool flag
        if index + 1 >= len(args) or args[index + 1].startswith("--"):
            payload[key] = True
            index += 1
            continue
        payload[key] = args[index + 1]
        index += 2
    return payload


def run_plan_then_auto(payload: dict) -> dict:
    """Run planner then auto-rounds pipeline (shared by legacy & FastAPI hubs)."""
    required = ["spec_file", "data", "value_col", "year_start", "year_end"]
    missing = missing_required_fields(payload, required)
    if missing:
        return {
            "ok": False,
            "stage": "input_validation",
            "error_code": "missing_required_fields",
            "error": f"missing required fields: {', '.join(missing)}",
            "missing_fields": missing,
            "plan": None,
            "auto_rounds": None,
        }

    plan_args = payload_to_args(payload, ["spec_file", "out_json", "out_md"])
    auto_args = payload_to_args(
        payload,
        [
            "data",
            "value_col",
            "key",
            "year_start",
            "year_end",
            "top_years",
            "keyword_name",
            "keyword_template1",
            "keyword_template2",
            "task_output",
            "max_rounds",
            "min_gain",
            "patience",
            # NOTE: agent_cmd / validate_cmd intentionally excluded
            # to prevent RCE via /plan-auto-rounds endpoint.
            "report",
        ],
    )

    plan_res = run_script("plan_research_workflow.py", plan_args)
    if not plan_res["ok"]:
        plan_error = (plan_res.get("stderr") or "").strip() or "plan stage failed"
        return {
            "ok": False,
            "stage": "plan",
            "error_code": "plan_failed",
            "error": plan_error,
            "plan": plan_res,
            "auto_rounds": None,
        }

    auto_res = run_script("run_auto_rounds.py", auto_args)
    if not auto_res["ok"]:
        auto_error = (auto_res.get("stderr") or "").strip() or "auto-rounds stage failed"
        return {
            "ok": False,
            "stage": "auto_rounds_failed",
            "error_code": "auto_rounds_failed",
            "error": auto_error,
            "plan": plan_res,
            "auto_rounds": auto_res,
        }

    return {
        "ok": True,
        "stage": "auto_rounds",
        "plan": plan_res,
        "auto_rounds": auto_res,
    }
