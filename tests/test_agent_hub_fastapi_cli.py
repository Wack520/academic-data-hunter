from __future__ import annotations

import sys

from scripts import agent_hub_fastapi


def test_serve_generates_ephemeral_key_when_missing(monkeypatch) -> None:
    created: dict[str, object] = {}
    run_called: dict[str, object] = {}

    def fake_create_app(api_key: str, max_request_body_bytes: int):
        created["api_key"] = api_key
        created["max_request_body_bytes"] = max_request_body_bytes
        return {"app": "fake"}

    def fake_uvicorn_run(app, host: str, port: int, log_level: str) -> None:
        run_called["app"] = app
        run_called["host"] = host
        run_called["port"] = port
        run_called["log_level"] = log_level

    monkeypatch.setattr(agent_hub_fastapi, "create_app", fake_create_app)
    monkeypatch.setattr(agent_hub_fastapi.uvicorn, "run", fake_uvicorn_run)
    monkeypatch.setattr(agent_hub_fastapi.secrets, "token_urlsafe", lambda _: "ephemeral-key")

    agent_hub_fastapi.serve("127.0.0.1", 9000, "")

    assert created["api_key"] == "ephemeral-key"
    assert run_called["host"] == "127.0.0.1"
    assert run_called["port"] == 9000
    assert run_called["log_level"] == "info"


def test_serve_uses_given_api_key(monkeypatch) -> None:
    created: dict[str, object] = {}
    run_called: dict[str, object] = {}

    monkeypatch.setattr(
        agent_hub_fastapi,
        "create_app",
        lambda api_key, max_request_body_bytes: (
            created.update({"api_key": api_key, "max_request_body_bytes": max_request_body_bytes}) or {"app": "fake"}
        ),
    )
    monkeypatch.setattr(
        agent_hub_fastapi.uvicorn,
        "run",
        lambda app, host, port, log_level: run_called.update(
            {"app": app, "host": host, "port": port, "log_level": log_level}
        ),
    )
    monkeypatch.setattr(agent_hub_fastapi.secrets, "token_urlsafe", lambda _: "unused")

    agent_hub_fastapi.serve("0.0.0.0", 9001, "explicit-key")

    assert created["api_key"] == "explicit-key"
    assert run_called["host"] == "0.0.0.0"
    assert run_called["port"] == 9001
    assert run_called["log_level"] == "info"


def test_main_calls_serve_with_cli_args(monkeypatch) -> None:
    called: dict[str, object] = {}
    monkeypatch.setattr(agent_hub_fastapi, "configure_logging", lambda: None)
    monkeypatch.setattr(
        agent_hub_fastapi,
        "serve",
        lambda host, port, api_key: called.update({"host": host, "port": port, "api_key": api_key}),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["agent_hub_fastapi.py", "--host", "127.0.0.1", "--port", "8788", "--api-key", "k-fastapi"],
    )

    agent_hub_fastapi.main()

    assert called == {"host": "127.0.0.1", "port": 8788, "api_key": "k-fastapi"}
