from __future__ import annotations

import sys
from collections.abc import Iterator

from scripts import agent_hub


def _input_iter(items: list[object]) -> Iterator[object]:
    yield from items


def test_chat_flow_covers_help_unknown_plan_auto_and_script_paths(monkeypatch) -> None:
    run_calls: list[tuple[str, list[str]]] = []
    plan_payloads: list[dict] = []
    inputs = _input_iter(
        [
            "help",
            "unknown_cmd --x 1",
            "run_round --data x.csv --value-col val --year-start 2020 --year-end 2021 --output task.md",
            "plan_auto_rounds --spec-file spec.json --data panel.csv --value-col val --year-start 2020 --year-end 2021",
            "qc_case01",
            "export_evidence_pack --data panel.csv --registry reg.csv --output-dir tmp/out --value-col val",
            "benchmark_eval --data panel.csv --registry reg.csv --output-json tmp/report.json --value-col val",
            "exit",
        ]
    )

    def fake_input(prompt: str = "") -> str:
        value = next(inputs)
        assert isinstance(value, str)
        return value

    def fake_run_script(script_name: str, args: list[str]) -> dict:
        run_calls.append((script_name, args))
        return {
            "ok": True,
            "returncode": 0,
            "command": [script_name, *args],
            "stdout": "stdout-ok\n",
            "stderr": "stderr-ok\n",
        }

    def fake_run_plan_then_auto(payload: dict) -> dict:
        plan_payloads.append(payload)
        return {
            "ok": True,
            "stage": "auto_rounds",
            "plan": {"stdout": "plan-stdout\n", "stderr": "plan-stderr\n"},
            "auto_rounds": {"stdout": "auto-stdout\n", "stderr": "auto-stderr\n"},
        }

    monkeypatch.setattr("builtins.input", fake_input)
    monkeypatch.setattr(agent_hub, "run_script", fake_run_script)
    monkeypatch.setattr(agent_hub, "run_plan_then_auto", fake_run_plan_then_auto)

    agent_hub.chat()

    assert run_calls[0][0] == "run_round.py"
    assert run_calls[1][0] == "cases/case01-nev-carbon/scripts/qc_case01.py"
    assert run_calls[2][0] == "export_evidence_pack.py"
    assert run_calls[3][0] == "run_benchmark_eval.py"
    assert plan_payloads == [
        {
            "spec_file": "spec.json",
            "data": "panel.csv",
            "value_col": "val",
            "year_start": "2020",
            "year_end": "2021",
        }
    ]


def test_chat_handles_eof(monkeypatch) -> None:
    def fake_input(prompt: str = "") -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", fake_input)
    agent_hub.chat()


def test_serve_generates_ephemeral_api_key(monkeypatch) -> None:
    events: dict[str, object] = {}

    class DummyServer:
        def __init__(self, addr, handler_cls):
            events["addr"] = addr
            events["handler_cls"] = handler_cls

        def serve_forever(self) -> None:
            events["served"] = True

    monkeypatch.setattr(agent_hub, "ThreadingHTTPServer", DummyServer)
    monkeypatch.setattr(agent_hub.secrets, "token_urlsafe", lambda n: "ephemeral-key")

    agent_hub.serve("127.0.0.1", 9876, "")

    assert agent_hub.AgentHandler.required_api_key == "ephemeral-key"
    assert events["addr"] == ("127.0.0.1", 9876)
    assert events["served"] is True


def test_main_serve_legacy_backend(monkeypatch) -> None:
    called: dict[str, object] = {}
    monkeypatch.setattr(agent_hub, "configure_logging", lambda: None)
    monkeypatch.setenv("ADH_AGENT_HUB_BACKEND", "legacy")
    monkeypatch.setattr(
        agent_hub,
        "serve",
        lambda host, port, api_key: called.update({"host": host, "port": port, "api_key": api_key}),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["agent_hub.py", "serve", "--host", "0.0.0.0", "--port", "9001", "--api-key", "k1"],
    )

    agent_hub.main()

    assert called == {"host": "0.0.0.0", "port": 9001, "api_key": "k1"}


def test_main_serve_fastapi_backend_success(monkeypatch) -> None:
    called: dict[str, object] = {}
    monkeypatch.setattr(agent_hub, "configure_logging", lambda: None)
    monkeypatch.delenv("ADH_AGENT_HUB_BACKEND", raising=False)
    import scripts.agent_hub_fastapi as fastapi_mod

    monkeypatch.setattr(
        fastapi_mod,
        "serve",
        lambda host, port, api_key: called.update({"host": host, "port": port, "api_key": api_key}),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["agent_hub.py", "serve", "--host", "127.0.0.1", "--port", "9002", "--api-key", "k2"],
    )

    agent_hub.main()

    assert called == {"host": "127.0.0.1", "port": 9002, "api_key": "k2"}


def test_main_serve_fastapi_backend_fallback_to_legacy(monkeypatch) -> None:
    called: dict[str, object] = {}
    monkeypatch.setattr(agent_hub, "configure_logging", lambda: None)
    monkeypatch.setenv("ADH_AGENT_HUB_BACKEND", "fastapi")
    import scripts.agent_hub_fastapi as fastapi_mod

    def broken_fastapi_serve(host: str, port: int, api_key: str) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(fastapi_mod, "serve", broken_fastapi_serve)
    monkeypatch.setattr(
        agent_hub,
        "serve",
        lambda host, port, api_key: called.update({"host": host, "port": port, "api_key": api_key}),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["agent_hub.py", "serve", "--host", "127.0.0.1", "--port", "9003", "--api-key", "k3"],
    )

    agent_hub.main()

    assert called == {"host": "127.0.0.1", "port": 9003, "api_key": "k3"}


def test_main_chat_mode(monkeypatch) -> None:
    called = {"chat": 0}
    monkeypatch.setattr(agent_hub, "configure_logging", lambda: None)
    monkeypatch.setattr(agent_hub, "chat", lambda: called.__setitem__("chat", called["chat"] + 1))
    monkeypatch.setattr(sys, "argv", ["agent_hub.py", "chat"])

    agent_hub.main()

    assert called["chat"] == 1
