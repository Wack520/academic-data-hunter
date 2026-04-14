from __future__ import annotations

import asyncio
from collections.abc import Generator

import pytest

pytest.importorskip("fastapi")

from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

from scripts import agent_hub_common, agent_hub_fastapi


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    app = agent_hub_fastapi.create_app(api_key="test-key", max_request_body_bytes=1024)
    with TestClient(app) as test_client:
        yield test_client


def test_health_requires_authorization(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 401
    assert response.json()["ok"] is False


def test_health_with_authorization(client: TestClient) -> None:
    response = client.get("/health", headers={"Authorization": "Bearer test-key"})
    assert response.status_code == 200
    assert response.json() == {"ok": True, "service": "academic-data-hunter-agent-hub"}


def test_parse_json_body_branches() -> None:
    assert agent_hub_fastapi._parse_json_body(b"") == {}
    assert agent_hub_fastapi._parse_json_body(b'{"a":1}') == {"a": 1}

    with pytest.raises(ValueError, match="invalid json"):
        agent_hub_fastapi._parse_json_body(b"{")

    with pytest.raises(ValueError, match="root must be object"):
        agent_hub_fastapi._parse_json_body(b"[]")


def test_auto_rounds_ignores_agent_cmd_and_validate_cmd(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
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

    monkeypatch.setattr(agent_hub_fastapi, "run_script", fake_run_script)

    response = client.post(
        "/auto-rounds",
        headers={"Authorization": "Bearer test-key"},
        json={
            "data": "cases/case01-nev-carbon/data/charging_piles_by_province.csv",
            "value_col": "public_charging_piles",
            "year_start": 2017,
            "year_end": 2023,
            "agent_cmd": "echo injected",
            "validate_cmd": "echo injected-validate",
        },
    )

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert calls[0][0] == "run_auto_rounds.py"
    forwarded_args = calls[0][1]
    assert "--agent-cmd" not in forwarded_args
    assert "--validate-cmd" not in forwarded_args


def test_plan_auto_rounds_ignores_agent_cmd_and_validate_cmd(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
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

    response = client.post(
        "/plan-auto-rounds",
        headers={"Authorization": "Bearer test-key"},
        json={
            "spec_file": "templates/research-spec-template.json",
            "data": "cases/case01-nev-carbon/data/charging_piles_by_province.csv",
            "value_col": "public_charging_piles",
            "year_start": 2017,
            "year_end": 2023,
            "agent_cmd": "echo injected",
            "validate_cmd": "echo injected-validate",
        },
    )

    assert response.status_code == 200
    assert response.json()["ok"] is True
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
    client: TestClient,
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

    monkeypatch.setattr(agent_hub_fastapi, "run_script", fake_run_script)

    response = client.post(path, headers={"Authorization": "Bearer test-key"}, json=payload)
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert calls and calls[0][0] == expected_script


@pytest.mark.parametrize(
    "path,payload",
    [
        (
            "/run-round",
            {"data": "x.csv", "value_col": "val", "year_start": 2020, "year_end": 2021, "output": "task.md"},
        ),
        (
            "/validate-round",
            {"data": "x.csv", "registry": "r.csv", "variable": "v", "value_col": "val"},
        ),
        (
            "/auto-rounds",
            {"data": "x.csv", "value_col": "val", "year_start": 2020, "year_end": 2021},
        ),
        (
            "/plan-workflow",
            {"spec_file": "templates/research-spec-template.json"},
        ),
        (
            "/qc-case01",
            {"no_strict_c_cross_check": True},
        ),
        (
            "/export-evidence-pack",
            {"data": "x.csv", "registry": "r.csv", "output_dir": "tmp/out"},
        ),
        (
            "/benchmark-eval",
            {"data": "x.csv", "registry": "r.csv", "output_json": "tmp/out.json"},
        ),
    ],
)
def test_post_routes_return_500_when_run_script_fails(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
    path: str,
    payload: dict,
) -> None:
    monkeypatch.setattr(
        agent_hub_fastapi,
        "run_script",
        lambda script_name, args: {
            "ok": False,
            "returncode": 1,
            "command": [script_name, *args],
            "stdout": "",
            "stderr": "boom",
        },
    )

    response = client.post(path, headers={"Authorization": "Bearer test-key"}, json=payload)
    assert response.status_code == 500
    assert response.json()["ok"] is False


def test_plan_auto_rounds_failure_returns_500(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
) -> None:
    monkeypatch.setattr(agent_hub_fastapi, "run_plan_then_auto", lambda payload: {"ok": False, "stage": "plan"})
    response = client.post(
        "/plan-auto-rounds",
        headers={"Authorization": "Bearer test-key"},
        json={
            "spec_file": "templates/research-spec-template.json",
            "data": "cases/case01-nev-carbon/data/charging_piles_by_province.csv",
            "value_col": "public_charging_piles",
            "year_start": 2017,
            "year_end": 2023,
        },
    )
    assert response.status_code == 500
    assert response.json()["ok"] is False


def test_plan_auto_rounds_input_validation_stage_returns_400(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
) -> None:
    monkeypatch.setattr(
        agent_hub_fastapi,
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
    response = client.post(
        "/plan-auto-rounds",
        headers={"Authorization": "Bearer test-key"},
        json={
            "spec_file": "templates/research-spec-template.json",
            "data": "cases/case01-nev-carbon/data/charging_piles_by_province.csv",
            "value_col": "public_charging_piles",
            "year_start": 2017,
            "year_end": 2023,
        },
    )
    assert response.status_code == 400
    assert response.json()["ok"] is False
    assert response.json()["stage"] == "input_validation"


def test_payload_too_large_returns_400() -> None:
    app = agent_hub_fastapi.create_app(api_key="test-key", max_request_body_bytes=8)
    with TestClient(app) as test_client:
        response = test_client.post(
            "/auto-rounds",
            headers={"Authorization": "Bearer test-key", "Content-Type": "application/json"},
            content='{"data":"123456789"}',
        )
    assert response.status_code == 400
    assert response.json()["ok"] is False


def test_invalid_json_and_invalid_root_return_400(client: TestClient) -> None:
    response = client.post(
        "/auto-rounds",
        headers={"Authorization": "Bearer test-key", "Content-Type": "application/json"},
        content="{not-json",
    )
    assert response.status_code == 400
    assert response.json()["ok"] is False
    assert "invalid json" in response.json()["error"]

    response = client.post(
        "/auto-rounds",
        headers={"Authorization": "Bearer test-key", "Content-Type": "application/json"},
        content="[]",
    )
    assert response.status_code == 400
    assert response.json()["ok"] is False
    assert "root must be object" in response.json()["error"]


@pytest.mark.parametrize(
    ("path", "payload", "expected_missing_fragment"),
    [
        ("/run-round", {"data": "x.csv", "value_col": "val"}, "year_start"),
        ("/validate-round", {"data": "x.csv", "registry": "r.csv"}, "variable"),
        ("/auto-rounds", {"data": "x.csv", "value_col": "val", "year_start": 2020}, "year_end"),
        ("/plan-workflow", {}, "spec_file"),
        ("/plan-auto-rounds", {"spec_file": "templates/research-spec-template.json"}, "data"),
        ("/export-evidence-pack", {"data": "x.csv", "registry": "r.csv"}, "output_dir"),
        ("/benchmark-eval", {"data": "x.csv", "registry": "r.csv"}, "output_json"),
    ],
)
def test_post_missing_required_fields_returns_400(
    client: TestClient,
    path: str,
    payload: dict,
    expected_missing_fragment: str,
) -> None:
    response = client.post(path, headers={"Authorization": "Bearer test-key"}, json=payload)
    assert response.status_code == 400
    assert response.json()["ok"] is False
    assert response.json()["stage"] == "input_validation"
    assert response.json()["error_code"] == "missing_required_fields"
    assert "missing required fields" in response.json()["error"]
    assert expected_missing_fragment in response.json()["error"]
    assert expected_missing_fragment in response.json()["missing_fields"]


def _build_request(*, app, method: str, path: str, headers: dict[str, str], body: bytes) -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("utf-8"),
        "query_string": b"",
        "headers": [(k.lower().encode("latin-1"), v.encode("latin-1")) for k, v in headers.items()],
        "client": ("testclient", 123),
        "server": ("testserver", 80),
        "root_path": "",
        "app": app,
    }
    sent = False

    async def receive() -> dict:
        nonlocal sent
        if sent:
            return {"type": "http.request", "body": b"", "more_body": False}
        sent = True
        return {"type": "http.request", "body": body, "more_body": False}

    return Request(scope, receive)


def test_middleware_invalid_content_length_and_raw_body_limit() -> None:
    app = agent_hub_fastapi.create_app(api_key="test-key", max_request_body_bytes=8)
    dispatch = app.user_middleware[0].kwargs["dispatch"]

    async def call_next(_: Request) -> JSONResponse:
        return JSONResponse({"ok": True})

    req_bad_len = _build_request(
        app=app,
        method="POST",
        path="/auto-rounds",
        headers={"Authorization": "Bearer test-key", "Content-Length": "abc"},
        body=b"{}",
    )
    resp_bad_len = asyncio.run(dispatch(req_bad_len, call_next))
    assert resp_bad_len.status_code == 400
    assert b"invalid Content-Length" in resp_bad_len.body

    req_bad_raw = _build_request(
        app=app,
        method="POST",
        path="/auto-rounds",
        headers={"Authorization": "Bearer test-key"},
        body=b"0123456789",
    )
    resp_bad_raw = asyncio.run(dispatch(req_bad_raw, call_next))
    assert resp_bad_raw.status_code == 400
    assert b"payload too large" in resp_bad_raw.body


def test_http_and_starlette_exception_handlers_cover_nonstr_branches() -> None:
    app = agent_hub_fastapi.create_app(api_key="", max_request_body_bytes=1024)

    @app.get("/raise-http-nonstr")
    async def raise_http_nonstr() -> dict:
        raise HTTPException(status_code=418, detail={"x": 1})

    @app.get("/raise-starlette-str")
    async def raise_starlette_str() -> dict:
        raise StarletteHTTPException(status_code=409, detail="bad-request")

    @app.get("/raise-starlette-nonstr")
    async def raise_starlette_nonstr() -> dict:
        raise StarletteHTTPException(status_code=410, detail={"x": 2})

    with TestClient(app) as test_client:
        resp = test_client.get("/raise-http-nonstr")
        assert resp.status_code == 418
        assert resp.json() == {"ok": False, "x": 1}

        resp = test_client.get("/raise-starlette-str")
        assert resp.status_code == 409
        assert resp.json() == {"ok": False, "error": "bad-request"}

        resp = test_client.get("/raise-starlette-nonstr")
        assert resp.status_code == 410
        assert resp.json() == {"ok": False, "error": "http error"}


def test_unknown_path_returns_legacy_compatible_404(client: TestClient) -> None:
    response = client.get("/not-exist", headers={"Authorization": "Bearer test-key"})
    assert response.status_code == 404
    assert response.json() == {"ok": False, "error": "not found"}
