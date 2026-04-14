from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _send(proc: subprocess.Popen[str], payload: dict) -> None:
    assert proc.stdin is not None
    proc.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
    proc.stdin.flush()


def _read_json_lines(proc: subprocess.Popen[str], *, limit: int = 10) -> list[dict]:
    assert proc.stdout is not None
    messages: list[dict] = []
    for _ in range(limit):
        line = proc.stdout.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        messages.append(json.loads(line))
        if messages and messages[-1].get("id") is not None:
            break
    return messages


def test_mcp_server_initialize_list_tools_and_call_tool(tmp_path: Path) -> None:
    data_path = tmp_path / "panel.csv"
    registry_path = tmp_path / "registry.csv"
    report_json = tmp_path / "benchmark.json"
    report_md = tmp_path / "benchmark.md"

    data_path.write_text(
        (
            "province,year,target_value,source_id,source_level,source_name,source_url,cross_check_url,access_date,note\n"
            "北京,2023,100,SRC_1,A,北京市统计局,https://a.gov.cn,,2026-04-14,\n"
        ),
        encoding="utf-8-sig",
    )
    registry_path.write_text(
        (
            "source_id,variable,source_level,source_name,source_url,cross_check_url,publish_date,access_date,evidence_file,is_primary,note\n"
            "SRC_1,target,A,北京市统计局,https://a.gov.cn,,2026-01-01,2026-04-14,,1,\n"
        ),
        encoding="utf-8-sig",
    )

    proc = subprocess.Popen(
        [sys.executable, "scripts/mcp_server.py"],
        cwd=ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        _send(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "pytest", "version": "1.0"},
                },
            },
        )
        init_messages = _read_json_lines(proc)
        assert init_messages[-1]["id"] == 1
        assert init_messages[-1]["result"]["capabilities"]["tools"] == {}

        _send(proc, {"jsonrpc": "2.0", "method": "notifications/initialized"})
        _send(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tool_messages = _read_json_lines(proc)
        tool_names = {tool["name"] for tool in tool_messages[-1]["result"]["tools"]}
        assert {
            "run_round",
            "validate_round",
            "export_evidence_pack",
            "benchmark_eval",
        }.issubset(tool_names)

        _send(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "benchmark_eval",
                    "arguments": {
                        "data": str(data_path),
                        "registry": str(registry_path),
                        "variable": "target",
                        "value_col": "target_value",
                        "year_start": 2023,
                        "year_end": 2023,
                        "output_json": str(report_json),
                        "output_md": str(report_md),
                    },
                },
            },
        )
        call_messages = _read_json_lines(proc)
        result = call_messages[-1]["result"]
        assert result["isError"] is False
        assert report_json.exists()
        assert report_md.exists()
        assert "overall_score" in result["structuredContent"]["metrics"]
    finally:
        if proc.stdin:
            try:
                _send(proc, {"jsonrpc": "2.0", "id": 99, "method": "shutdown"})
                _read_json_lines(proc)
                _send(proc, {"jsonrpc": "2.0", "method": "exit"})
            except Exception:
                pass
        proc.terminate()
        proc.wait(timeout=5)
