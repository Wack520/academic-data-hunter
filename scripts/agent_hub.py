"""
Hybrid Agent Hub

同一份能力，支持两种模式：
1) API 进程模式（serve）
2) 交互式 REPL 模式（chat）

示例：
  # 启动HTTP API
  python scripts/agent_hub.py serve --host 127.0.0.1 --port 8787

  # 启动交互式Agent
  python scripts/agent_hub.py chat
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import secrets
import shlex
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

try:
    from scripts.agent_hub_common import (
        args_list_to_payload,
        missing_required_fields,
        payload_to_args,
        run_plan_then_auto,
        run_script,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    from agent_hub_common import (
        args_list_to_payload,
        missing_required_fields,
        payload_to_args,
        run_plan_then_auto,
        run_script,
    )
from tools.config import (
    AGENT_HUB_DEFAULT_HOST,
    AGENT_HUB_DEFAULT_PORT,
    AGENT_HUB_MAX_REQUEST_BODY_BYTES,
)
from tools.logging_utils import configure_logging

MAX_REQUEST_BODY_BYTES = AGENT_HUB_MAX_REQUEST_BODY_BYTES


class AgentHandler(BaseHTTPRequestHandler):
    required_api_key: str = ""
    max_request_body_bytes: int = MAX_REQUEST_BODY_BYTES

    def _send_json(self, code: int, body: dict):
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _authorized(self) -> bool:
        if not self.required_api_key:
            return True
        auth = (self.headers.get("Authorization") or "").strip()
        return auth == f"Bearer {self.required_api_key}"

    def _require_auth(self) -> bool:
        if self._authorized():
            return True
        self._send_json(401, {"ok": False, "error": "unauthorized"})
        return False

    def _read_json(self) -> dict:
        length_header = self.headers.get("Content-Length", "0")
        try:
            length = int(length_header)
        except ValueError as e:
            raise ValueError(f"invalid Content-Length: {length_header!r}") from e
        if length <= 0:
            return {}
        if length > self.max_request_body_bytes:
            raise ValueError(f"payload too large: {length} bytes (max {self.max_request_body_bytes})")
        raw = self.rfile.read(length)
        if len(raw) > self.max_request_body_bytes:
            raise ValueError(f"payload too large: {len(raw)} bytes (max {self.max_request_body_bytes})")
        return json.loads(raw.decode("utf-8"))

    def _reject_missing_required(self, payload: dict, required: list[str]) -> bool:
        missing = missing_required_fields(payload, required)
        if not missing:
            return False
        self._send_json(
            400,
            {
                "ok": False,
                "stage": "input_validation",
                "error_code": "missing_required_fields",
                "error": f"missing required fields: {', '.join(missing)}",
                "missing_fields": missing,
            },
        )
        return True

    def do_GET(self):
        if not self._require_auth():
            return
        if self.path == "/health":
            self._send_json(200, {"ok": True, "service": "academic-data-hunter-agent-hub"})
            return
        self._send_json(404, {"ok": False, "error": "not found"})

    def do_POST(self):
        if not self._require_auth():
            return
        try:
            payload = self._read_json()
        except Exception as e:
            self._send_json(400, {"ok": False, "error": f"invalid json: {e}"})
            return

        if self.path == "/run-round":
            if self._reject_missing_required(payload, ["data", "value_col", "year_start", "year_end", "output"]):
                return
            args = payload_to_args(
                payload,
                [
                    "data",
                    "value_col",
                    "year_start",
                    "year_end",
                    "top_years",
                    "keyword_name",
                    "keyword_template1",
                    "keyword_template2",
                    "output",
                ],
            )
            res = run_script("run_round.py", args)
            self._send_json(200 if res["ok"] else 500, res)
            return

        if self.path == "/validate-round":
            if self._reject_missing_required(payload, ["data", "registry", "variable"]):
                return
            args = payload_to_args(
                payload,
                [
                    "data",
                    "registry",
                    "variable",
                    "key",
                    "required",
                    "value_col",
                    "check_unit",
                    "strict_c_cross_check",
                ],
            )
            res = run_script("validate_round.py", args)
            self._send_json(200 if res["ok"] else 500, res)
            return

        if self.path == "/auto-rounds":
            if self._reject_missing_required(payload, ["data", "value_col", "year_start", "year_end"]):
                return
            args = payload_to_args(
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
                    # from API surface to prevent command injection.
                    # Use CLI chat mode for custom agent commands.
                    "report",
                ],
            )
            res = run_script("run_auto_rounds.py", args)
            self._send_json(200 if res["ok"] else 500, res)
            return

        if self.path == "/plan-workflow":
            if self._reject_missing_required(payload, ["spec_file"]):
                return
            args = payload_to_args(
                payload,
                [
                    "spec_file",
                    "out_json",
                    "out_md",
                ],
            )
            res = run_script("plan_research_workflow.py", args)
            self._send_json(200 if res["ok"] else 500, res)
            return

        if self.path == "/plan-auto-rounds":
            if self._reject_missing_required(payload, ["spec_file", "data", "value_col", "year_start", "year_end"]):
                return
            res = run_plan_then_auto(payload)
            stage = (res or {}).get("stage")
            status = 200 if res.get("ok") else (400 if stage == "input_validation" else 500)
            self._send_json(status, res)
            return

        if self.path == "/qc-case01":
            args = payload_to_args(payload, ["no_strict_c_cross_check"])
            res = run_script("cases/case01-nev-carbon/scripts/qc_case01.py", args)
            self._send_json(200 if res["ok"] else 500, res)
            return

        if self.path == "/export-evidence-pack":
            if self._reject_missing_required(payload, ["data", "registry", "output_dir"]):
                return
            args = payload_to_args(
                payload,
                [
                    "data",
                    "registry",
                    "output_dir",
                    "variable",
                    "value_col",
                    "key",
                ],
            )
            res = run_script("export_evidence_pack.py", args)
            self._send_json(200 if res["ok"] else 500, res)
            return

        if self.path == "/benchmark-eval":
            if self._reject_missing_required(payload, ["data", "registry", "output_json"]):
                return
            args = payload_to_args(
                payload,
                [
                    "data",
                    "registry",
                    "output_json",
                    "output_md",
                    "variable",
                    "value_col",
                    "key",
                    "year_start",
                    "year_end",
                ],
            )
            res = run_script("run_benchmark_eval.py", args)
            self._send_json(200 if res["ok"] else 500, res)
            return

        self._send_json(404, {"ok": False, "error": "not found"})


def serve(host: str, port: int, api_key: str):
    AgentHandler.required_api_key = (api_key or "").strip()
    if not AgentHandler.required_api_key:
        AgentHandler.required_api_key = secrets.token_urlsafe(24)
        logging.warning("No --api-key provided, generated ephemeral API key: %s", AgentHandler.required_api_key)
    server = ThreadingHTTPServer((host, port), AgentHandler)
    logging.info("Agent API running at http://%s:%s", host, port)
    logging.info("Auth: enabled (Authorization: Bearer <api-key>)")
    logging.info(
        "Endpoints: GET /health, POST /run-round, /validate-round, "
        "/auto-rounds, /plan-workflow, /plan-auto-rounds, /qc-case01, "
        "/export-evidence-pack, /benchmark-eval"
    )
    server.serve_forever()


def chat():
    logging.info("Academic Data Hunter Interactive Agent")
    logging.info(
        "commands: run_round ..., validate_round ..., auto_rounds ..., "
        "plan_workflow ..., plan_auto_rounds ..., qc_case01, export_evidence_pack ..., "
        "benchmark_eval ..., exit"
    )
    while True:
        try:
            line = input("agent> ").strip()
        except (EOFError, KeyboardInterrupt):
            logging.info("bye")
            break
        if not line:
            continue
        if line in {"exit", "quit"}:
            logging.info("bye")
            break
        if line == "help":
            logging.info("示例:")
            logging.info("  run_round --data ... --value-col ... --year-start 2017 --year-end 2023 --output ...")
            logging.info(
                "  validate_round --data ... --registry ... --variable charging --value-col ... --check-unit 台"
            )
            logging.info("  auto_rounds --data ... --value-col ... --year-start 2017 --year-end 2023")
            logging.info("  plan_workflow --spec-file templates/research-spec-template.json")
            logging.info(
                "  plan_auto_rounds --spec-file ... --data ... --value-col ... --year-start ... --year-end ..."
            )
            logging.info("  qc_case01")
            logging.info("  export_evidence_pack --data ... --registry ... --output-dir ... --value-col ...")
            logging.info("  benchmark_eval --data ... --registry ... --output-json ... --value-col ...")
            continue

        parts = shlex.split(line)
        cmd = parts[0]
        args = parts[1:]
        mapping = {
            "run_round": "run_round.py",
            "validate_round": "validate_round.py",
            "auto_rounds": "run_auto_rounds.py",
            "plan_workflow": "plan_research_workflow.py",
            "qc_case01": "cases/case01-nev-carbon/scripts/qc_case01.py",
            "export_evidence_pack": "export_evidence_pack.py",
            "benchmark_eval": "run_benchmark_eval.py",
        }
        if cmd == "plan_auto_rounds":
            payload = args_list_to_payload(args)
            res = run_plan_then_auto(payload)
            if res.get("plan", {}).get("stdout"):
                logging.info("%s", res["plan"]["stdout"].rstrip())
            if res.get("plan", {}).get("stderr"):
                logging.error("%s", res["plan"]["stderr"].rstrip())
            auto = res.get("auto_rounds") or {}
            if auto.get("stdout"):
                logging.info("%s", auto["stdout"].rstrip())
            if auto.get("stderr"):
                logging.error("%s", auto["stderr"].rstrip())
            logging.info("[ok=%s stage=%s]", res.get("ok"), res.get("stage"))
            continue
        if cmd not in mapping:
            logging.warning("unknown command: %s", cmd)
            continue
        res = run_script(mapping[cmd], args)
        if res["stdout"]:
            logging.info("%s", res["stdout"].rstrip())
        if res["stderr"]:
            logging.error("%s", res["stderr"].rstrip())
        logging.info("[exit=%s]", res["returncode"])


def main():
    configure_logging()
    parser = argparse.ArgumentParser(description="Hybrid Agent Hub")
    sub = parser.add_subparsers(dest="mode", required=True)

    p_serve = sub.add_parser("serve", help="启动API服务")
    p_serve.add_argument("--host", default=AGENT_HUB_DEFAULT_HOST)
    p_serve.add_argument("--port", type=int, default=AGENT_HUB_DEFAULT_PORT)
    p_serve.add_argument(
        "--api-key",
        default=os.environ.get("AGENT_HUB_API_KEY", ""),
        help="API鉴权密钥（请求头需传 Authorization: Bearer <key>）",
    )

    sub.add_parser("chat", help="启动交互式模式")

    args = parser.parse_args()
    if args.mode == "serve":
        backend = (os.environ.get("ADH_AGENT_HUB_BACKEND", "fastapi") or "fastapi").strip().lower()
        if backend == "legacy":
            serve(args.host, args.port, args.api_key)
            return
        try:
            from scripts.agent_hub_fastapi import serve as fastapi_serve

            logging.info("Using FastAPI backend for serve mode (set ADH_AGENT_HUB_BACKEND=legacy to fallback)")
            fastapi_serve(args.host, args.port, args.api_key)
            return
        except Exception as exc:
            logging.warning("FastAPI backend unavailable, fallback to legacy server: %s", exc)
            serve(args.host, args.port, args.api_key)
    elif args.mode == "chat":
        chat()


if __name__ == "__main__":
    main()
