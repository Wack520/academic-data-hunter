from __future__ import annotations

import json
import threading
from collections.abc import Generator
from http.server import ThreadingHTTPServer
from urllib import error, request

import pytest

from scripts import agent_hub


def _http_json(
    method: str, url: str, payload: dict | None = None, headers: dict[str, str] | None = None
) -> tuple[int, dict]:
    data = None
    req_headers = dict(headers or {})
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        req_headers.setdefault("Content-Type", "application/json")
    req = request.Request(url=url, data=data, headers=req_headers, method=method)
    try:
        with request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode("utf-8")
            return resp.getcode(), json.loads(body)
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        return exc.code, json.loads(body)


@pytest.fixture
def hub_server(monkeypatch: pytest.MonkeyPatch) -> Generator[tuple[str, str], None, None]:
    monkeypatch.setattr(agent_hub.AgentHandler, "log_message", lambda self, fmt, *args: None)
    agent_hub.AgentHandler.required_api_key = "test-key"
    server = ThreadingHTTPServer(("127.0.0.1", 0), agent_hub.AgentHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    host, port = server.server_address
    base_url = f"http://{host}:{port}"
    try:
        yield base_url, "test-key"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_health_requires_authorization(hub_server: tuple[str, str]) -> None:
    base_url, _ = hub_server
    status, body = _http_json("GET", f"{base_url}/health")
    assert status == 401
    assert body["ok"] is False


def test_auto_rounds_ignores_agent_cmd_and_validate_cmd(
    monkeypatch: pytest.MonkeyPatch,
    hub_server: tuple[str, str],
) -> None:
    calls: list[tuple[str, list[str]]] = []

    def fake_run_script(script_name: str, args: list[str]) -> dict:
        calls.append((script_name, args))
        return {
            "ok": True,
            "returncode": 0,
            "command": [script_name, *args],
            "stdout": "",
            "stderr": "",
        }

    monkeypatch.setattr(agent_hub, "run_script", fake_run_script)

    base_url, api_key = hub_server
    status, body = _http_json(
        "POST",
        f"{base_url}/auto-rounds",
        payload={
            "data": "cases/case01-nev-carbon/data/charging_piles_by_province.csv",
            "value_col": "public_charging_piles",
            "year_start": 2017,
            "year_end": 2023,
            "agent_cmd": "echo injected",
            "validate_cmd": "echo injected-validate",
        },
        headers={"Authorization": f"Bearer {api_key}"},
    )

    assert status == 200
    assert body["ok"] is True
    assert calls[0][0] == "run_auto_rounds.py"
    forwarded_args = calls[0][1]
    assert "--agent-cmd" not in forwarded_args
    assert "--validate-cmd" not in forwarded_args


def test_plan_auto_rounds_ignores_agent_cmd_and_validate_cmd(
    monkeypatch: pytest.MonkeyPatch,
    hub_server: tuple[str, str],
) -> None:
    calls: list[tuple[str, list[str]]] = []

    def fake_run_script(script_name: str, args: list[str]) -> dict:
        calls.append((script_name, args))
        return {
            "ok": True,
            "returncode": 0,
            "command": [script_name, *args],
            "stdout": "",
            "stderr": "",
        }

    monkeypatch.setattr(agent_hub, "run_script", fake_run_script)

    base_url, api_key = hub_server
    status, body = _http_json(
        "POST",
        f"{base_url}/plan-auto-rounds",
        payload={
            "spec_file": "templates/research-spec-template.json",
            "data": "cases/case01-nev-carbon/data/charging_piles_by_province.csv",
            "value_col": "public_charging_piles",
            "year_start": 2017,
            "year_end": 2023,
            "agent_cmd": "echo injected",
            "validate_cmd": "echo injected-validate",
        },
        headers={"Authorization": f"Bearer {api_key}"},
    )

    assert status == 200
    assert body["ok"] is True
    assert len(calls) == 2
    assert calls[0][0] == "plan_research_workflow.py"
    assert calls[1][0] == "run_auto_rounds.py"
    forwarded_args = calls[1][1]
    assert "--agent-cmd" not in forwarded_args
    assert "--validate-cmd" not in forwarded_args
