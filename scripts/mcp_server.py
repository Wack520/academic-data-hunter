#!/usr/bin/env python3
"""
Minimal stdio MCP server for Academic Data Hunter.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from typing import Any

try:
    from scripts.agent_hub_common import run_script
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    from agent_hub_common import run_script

PROTOCOL_VERSION = "2025-11-25"


@dataclass(frozen=True)
class ToolSpec:
    name: str
    title: str
    description: str
    script_name: str
    required: tuple[str, ...]
    optional: tuple[str, ...]

    @property
    def input_schema(self) -> dict[str, Any]:
        properties: dict[str, dict[str, Any]] = {}
        for field in (*self.required, *self.optional):
            properties[field] = {"type": "string", "description": field.replace("_", " ")}
        for field in ("year_start", "year_end"):
            if field in properties:
                properties[field]["type"] = "integer"
        return {
            "type": "object",
            "properties": properties,
            "required": list(self.required),
            "additionalProperties": False,
        }


TOOLS: dict[str, ToolSpec] = {
    "run_round": ToolSpec(
        name="run_round",
        title="Generate next-round task",
        description="Generate the next missing-data task file for a research dataset.",
        script_name="run_round.py",
        required=("data", "value_col", "year_start", "year_end", "output"),
        optional=("top_years", "keyword_name", "keyword_template1", "keyword_template2"),
    ),
    "validate_round": ToolSpec(
        name="validate_round",
        title="Validate dataset and registry",
        description="Run QC and source-registry consistency validation for a research dataset.",
        script_name="validate_round.py",
        required=("data", "registry", "variable"),
        optional=("value_col", "check_unit", "strict_c_cross_check", "key", "required"),
    ),
    "export_evidence_pack": ToolSpec(
        name="export_evidence_pack",
        title="Export evidence pack",
        description="Export an evidence-backed delivery bundle for a research-agent run.",
        script_name="export_evidence_pack.py",
        required=("data", "registry", "output_dir"),
        optional=("variable", "value_col", "key"),
    ),
    "benchmark_eval": ToolSpec(
        name="benchmark_eval",
        title="Run benchmark eval",
        description="Score a research-data run on coverage and provenance quality.",
        script_name="run_benchmark_eval.py",
        required=("data", "registry", "output_json"),
        optional=("output_md", "variable", "value_col", "key", "year_start", "year_end"),
    ),
}


def _write(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def _response(message_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": message_id, "result": result}


def _error(message_id: Any, code: int, message: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"jsonrpc": "2.0", "id": message_id, "error": {"code": code, "message": message}}
    if data is not None:
        payload["error"]["data"] = data
    return payload


def _tool_list_result() -> dict[str, Any]:
    return {
        "tools": [
            {
                "name": tool.name,
                "title": tool.title,
                "description": tool.description,
                "inputSchema": tool.input_schema,
            }
            for tool in TOOLS.values()
        ]
    }


def _normalize_arguments(arguments: dict[str, Any], tool: ToolSpec) -> list[str]:
    allow_keys = [*tool.required, *tool.optional]
    normalized: dict[str, Any] = {}
    for key in allow_keys:
        if key not in arguments:
            continue
        value = arguments[key]
        if isinstance(value, bool):
            normalized[key] = value
        elif value is None:
            continue
        else:
            normalized[key] = str(value)
    try:
        from scripts.agent_hub_common import payload_to_args
    except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
        from agent_hub_common import payload_to_args

    return payload_to_args(normalized, allow_keys)


def _parse_stdout(stdout_text: str) -> dict[str, Any] | None:
    raw = (stdout_text or "").strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def _tool_call_result(tool: ToolSpec, arguments: dict[str, Any]) -> dict[str, Any]:
    missing = [key for key in tool.required if key not in arguments or arguments[key] in {None, ""}]
    if missing:
        return {
            "content": [{"type": "text", "text": f"missing required arguments: {', '.join(missing)}"}],
            "isError": True,
            "structuredContent": {"missing": missing},
        }
    args = _normalize_arguments(arguments, tool)
    result = run_script(tool.script_name, args)
    stdout_text = result.get("stdout", "") or ""
    stderr_text = result.get("stderr", "") or ""
    structured = {
        "tool": tool.name,
        "command": result.get("command", []),
        "returncode": result.get("returncode", 1),
        "stdout": stdout_text,
        "stderr": stderr_text,
    }
    parsed_stdout = _parse_stdout(stdout_text)
    if parsed_stdout is not None:
        structured.update(parsed_stdout)
    text_blocks = []
    if stdout_text.strip():
        text_blocks.append(stdout_text.strip())
    if stderr_text.strip():
        text_blocks.append(stderr_text.strip())
    if not text_blocks:
        text_blocks.append(json.dumps({"ok": result.get("ok", False)}, ensure_ascii=False))
    return {
        "content": [{"type": "text", "text": "\n\n".join(text_blocks)}],
        "isError": not bool(result.get("ok")),
        "structuredContent": structured,
    }


def _handle_request(method: str, params: dict[str, Any], initialized: bool) -> tuple[dict[str, Any] | None, bool]:
    if method == "initialize":
        result = {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name": "academic-data-hunter",
                "title": "Academic Data Hunter MCP Server",
                "version": "0.1.0",
                "description": "Provenance-first tools for research data agents.",
            },
        }
        return result, initialized
    if method == "ping":
        return {}, initialized
    if method == "tools/list":
        if not initialized:
            raise ValueError("server not initialized")
        return _tool_list_result(), initialized
    if method == "tools/call":
        if not initialized:
            raise ValueError("server not initialized")
        tool_name = str(params.get("name", "")).strip()
        if tool_name not in TOOLS:
            raise KeyError(f"Unknown tool: {tool_name}")
        arguments = params.get("arguments") or {}
        if not isinstance(arguments, dict):
            raise TypeError("arguments must be an object")
        return _tool_call_result(TOOLS[tool_name], arguments), initialized
    if method == "shutdown":
        return {}, initialized
    if method == "notifications/initialized":
        return None, True
    if method == "exit":
        raise SystemExit(0)
    raise KeyError(f"Method not found: {method}")


def main() -> int:
    initialized = False
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = message.get("method")
        params = message.get("params") or {}
        message_id = message.get("id")

        try:
            result, maybe_initialized = _handle_request(str(method or ""), params, initialized)
            initialized = maybe_initialized
            if message_id is not None and result is not None:
                _write(_response(message_id, result))
        except SystemExit:
            break
        except KeyError as exc:
            if message_id is not None:
                _write(_error(message_id, -32601, str(exc)))
        except (TypeError, ValueError) as exc:
            if message_id is not None:
                _write(_error(message_id, -32602, str(exc)))
        except Exception as exc:  # pragma: no cover - defensive
            if message_id is not None:
                _write(_error(message_id, -32000, str(exc)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
