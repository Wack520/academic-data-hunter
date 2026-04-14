from __future__ import annotations

import http.client
import json
import threading
from collections.abc import Generator
from http.server import ThreadingHTTPServer
from urllib import error, request
from urllib.parse import urlparse

import pytest

from scripts import agent_hub, agent_hub_common


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


def _http_raw(
    method: str,
    url: str,
    raw: str,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict]:
    req = request.Request(url=url, data=raw.encode("utf-8"), headers=dict(headers or {}), method=method)
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


def test_health_with_authorization_and_unknown_get(hub_server: tuple[str, str]) -> None:
    base_url, api_key = hub_server
    status, body = _http_json("GET", f"{base_url}/health", headers={"Authorization": f"Bearer {api_key}"})
    assert status == 200
    assert body["ok"] is True
    assert body["service"] == "academic-data-hunter-agent-hub"

    status, body = _http_json("GET", f"{base_url}/not-found", headers={"Authorization": f"Bearer {api_key}"})
    assert status == 404
    assert body == {"ok": False, "error": "not found"}


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

    monkeypatch.setattr(agent_hub_common, "run_script", fake_run_script)

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


@pytest.mark.parametrize(
    ("path", "payload", "expected_script"),
    [
        (
            "/run-round",
            {
                "data": "cases/case01-nev-carbon/data/charging_piles_by_province.csv",
                "value_col": "public_charging_piles",
                "year_start": 2017,
                "year_end": 2023,
                "output": "next-round-task.md",
            },
            "run_round.py",
        ),
        (
            "/validate-round",
            {
                "data": "cases/case01-nev-carbon/data/charging_piles_by_province.csv",
                "registry": "cases/case01-nev-carbon/data/source_registry.csv",
                "variable": "charging",
                "value_col": "public_charging_piles",
            },
            "validate_round.py",
        ),
        (
            "/plan-workflow",
            {
                "spec_file": "templates/research-spec-template.json",
            },
            "plan_research_workflow.py",
        ),
        (
            "/qc-case01",
            {
                "no_strict_c_cross_check": True,
            },
            "cases/case01-nev-carbon/scripts/qc_case01.py",
        ),
        (
            "/export-evidence-pack",
            {
                "data": "cases/case01-nev-carbon/data/charging_piles_by_province.csv",
                "registry": "cases/case01-nev-carbon/data/source_registry.csv",
                "output_dir": "tmp/evidence-pack/case01",
                "value_col": "public_charging_piles",
            },
            "export_evidence_pack.py",
        ),
        (
            "/benchmark-eval",
            {
                "data": "cases/case01-nev-carbon/data/charging_piles_by_province.csv",
                "registry": "cases/case01-nev-carbon/data/source_registry.csv",
                "output_json": "tmp/benchmark/case01.json",
                "variable": "charging",
                "value_col": "public_charging_piles",
            },
            "run_benchmark_eval.py",
        ),
    ],
)
def test_post_routes_call_expected_script(
    monkeypatch: pytest.MonkeyPatch,
    hub_server: tuple[str, str],
    path: str,
    payload: dict,
    expected_script: str,
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
        f"{base_url}{path}",
        payload=payload,
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert status == 200
    assert body["ok"] is True
    assert calls and calls[0][0] == expected_script


def test_post_unknown_path_returns_404(hub_server: tuple[str, str]) -> None:
    base_url, api_key = hub_server
    status, body = _http_json(
        "POST",
        f"{base_url}/not-found",
        payload={},
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert status == 404
    assert body == {"ok": False, "error": "not found"}


def test_post_invalid_json_returns_400(hub_server: tuple[str, str]) -> None:
    base_url, api_key = hub_server
    status, body = _http_raw(
        "POST",
        f"{base_url}/auto-rounds",
        raw="{not-json",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    assert status == 400
    assert body["ok"] is False
    assert "invalid json" in body["error"]


def test_invalid_content_length_returns_400(hub_server: tuple[str, str]) -> None:
    base_url, api_key = hub_server
    parsed = urlparse(base_url)
    conn = http.client.HTTPConnection(parsed.hostname, parsed.port, timeout=5)
    conn.putrequest("POST", "/auto-rounds")
    conn.putheader("Authorization", f"Bearer {api_key}")
    conn.putheader("Content-Type", "application/json")
    conn.putheader("Content-Length", "abc")
    conn.endheaders()
    response = conn.getresponse()
    body = json.loads(response.read().decode("utf-8"))
    conn.close()

    assert response.status == 400
    assert body["ok"] is False
    assert "invalid Content-Length" in body["error"]


def test_payload_too_large_returns_400(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(agent_hub.AgentHandler, "log_message", lambda self, fmt, *args: None)
    agent_hub.AgentHandler.required_api_key = "test-key"
    agent_hub.AgentHandler.max_request_body_bytes = 8
    server = ThreadingHTTPServer(("127.0.0.1", 0), agent_hub.AgentHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    host, port = server.server_address
    base_url = f"http://{host}:{port}"
    try:
        status, body = _http_raw(
            "POST",
            f"{base_url}/auto-rounds",
            raw='{"data":"123456789"}',
            headers={
                "Authorization": "Bearer test-key",
                "Content-Type": "application/json",
            },
        )
        assert status == 400
        assert body["ok"] is False
        assert "payload too large" in body["error"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
        agent_hub.AgentHandler.max_request_body_bytes = agent_hub.MAX_REQUEST_BODY_BYTES


def test_plan_auto_rounds_failure_returns_500(
    monkeypatch: pytest.MonkeyPatch,
    hub_server: tuple[str, str],
) -> None:
    monkeypatch.setattr(agent_hub, "run_plan_then_auto", lambda payload: {"ok": False, "stage": "plan"})
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
        },
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert status == 500
    assert body["ok"] is False


def test_plan_auto_rounds_input_validation_stage_returns_400(
    monkeypatch: pytest.MonkeyPatch,
    hub_server: tuple[str, str],
) -> None:
    monkeypatch.setattr(
        agent_hub,
        "run_plan_then_auto",
        lambda payload: {
            "ok": False,
            "stage": "input_validation",
            "error_code": "missing_required_fields",
            "error": "missing required fields: data",
            "missing_fields": ["data"],
            "plan": None,
            "auto_rounds": None,
        },
    )
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
        },
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert status == 400
    assert body["ok"] is False
    assert body["stage"] == "input_validation"


def test_run_round_failure_returns_500(
    monkeypatch: pytest.MonkeyPatch,
    hub_server: tuple[str, str],
) -> None:
    monkeypatch.setattr(
        agent_hub,
        "run_script",
        lambda script_name, args: {
            "ok": False,
            "returncode": 1,
            "command": [script_name, *args],
            "stdout": "",
            "stderr": "boom",
        },
    )
    base_url, api_key = hub_server
    status, body = _http_json(
        "POST",
        f"{base_url}/run-round",
        payload={"data": "x.csv", "value_col": "val", "year_start": 2020, "year_end": 2021, "output": "task.md"},
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert status == 500
    assert body["ok"] is False


def test_export_evidence_pack_failure_returns_500(
    monkeypatch: pytest.MonkeyPatch,
    hub_server: tuple[str, str],
) -> None:
    monkeypatch.setattr(
        agent_hub,
        "run_script",
        lambda script_name, args: {
            "ok": False,
            "returncode": 1,
            "command": [script_name, *args],
            "stdout": "",
            "stderr": "boom",
        },
    )
    base_url, api_key = hub_server
    status, body = _http_json(
        "POST",
        f"{base_url}/export-evidence-pack",
        payload={"data": "x.csv", "registry": "r.csv", "output_dir": "tmp/out"},
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert status == 500
    assert body["ok"] is False


def test_benchmark_eval_failure_returns_500(
    monkeypatch: pytest.MonkeyPatch,
    hub_server: tuple[str, str],
) -> None:
    monkeypatch.setattr(
        agent_hub,
        "run_script",
        lambda script_name, args: {
            "ok": False,
            "returncode": 1,
            "command": [script_name, *args],
            "stdout": "",
            "stderr": "boom",
        },
    )
    base_url, api_key = hub_server
    status, body = _http_json(
        "POST",
        f"{base_url}/benchmark-eval",
        payload={"data": "x.csv", "registry": "r.csv", "output_json": "tmp/out.json"},
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert status == 500
    assert body["ok"] is False


def test_server_without_api_key_allows_request(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(agent_hub.AgentHandler, "log_message", lambda self, fmt, *args: None)
    agent_hub.AgentHandler.required_api_key = ""
    server = ThreadingHTTPServer(("127.0.0.1", 0), agent_hub.AgentHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    host, port = server.server_address
    base_url = f"http://{host}:{port}"
    try:
        status, body = _http_json("GET", f"{base_url}/health")
        assert status == 200
        assert body["ok"] is True
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


@pytest.mark.parametrize(
    ("path", "payload", "expected_missing_fragment"),
    [
        ("/run-round", {"data": "x.csv", "value_col": "v"}, "year_start"),
        ("/validate-round", {"data": "x.csv", "registry": "r.csv"}, "variable"),
        ("/auto-rounds", {"data": "x.csv", "value_col": "v", "year_start": 2020}, "year_end"),
        ("/plan-workflow", {}, "spec_file"),
        (
            "/plan-auto-rounds",
            {"spec_file": "templates/research-spec-template.json"},
            "data",
        ),
        ("/export-evidence-pack", {"data": "x.csv", "registry": "r.csv"}, "output_dir"),
        ("/benchmark-eval", {"data": "x.csv", "registry": "r.csv"}, "output_json"),
    ],
)
def test_post_missing_required_fields_returns_400(
    hub_server: tuple[str, str],
    path: str,
    payload: dict,
    expected_missing_fragment: str,
) -> None:
    base_url, api_key = hub_server
    status, body = _http_json(
        "POST",
        f"{base_url}{path}",
        payload=payload,
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert status == 400
    assert body["ok"] is False
    assert body["stage"] == "input_validation"
    assert body["error_code"] == "missing_required_fields"
    assert "missing required fields" in body["error"]
    assert expected_missing_fragment in body["error"]
    assert expected_missing_fragment in body["missing_fields"]
