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
import shlex
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def run_script(script_name: str, args: list[str]) -> dict:
    if "/" in script_name or os.path.sep in script_name:
        script_path = os.path.join(ROOT, script_name)
    else:
        script_path = os.path.join(ROOT, "scripts", script_name)
    cmd = [sys.executable, script_path] + args
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "command": cmd,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def run_plan_then_auto(payload: dict) -> dict:
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
            "agent_cmd",
            "validate_cmd",
            "report",
        ],
    )

    plan_res = run_script("plan_research_workflow.py", plan_args)
    if not plan_res["ok"]:
        return {
            "ok": False,
            "stage": "plan",
            "plan": plan_res,
            "auto_rounds": None,
        }

    auto_res = run_script("run_auto_rounds.py", auto_args)
    return {
        "ok": auto_res["ok"],
        "stage": "auto_rounds" if auto_res["ok"] else "auto_rounds_failed",
        "plan": plan_res,
        "auto_rounds": auto_res,
    }


def payload_to_args(payload: dict, allow_keys: list[str]) -> list[str]:
    args: list[str] = []
    for k in allow_keys:
        if k not in payload:
            continue
        v = payload[k]
        flag = f"--{k.replace('_', '-')}"
        if isinstance(v, bool):
            if v:
                args.append(flag)
            continue
        if v is None:
            continue
        args.extend([flag, str(v)])
    return args


def args_list_to_payload(args: list[str]) -> dict:
    payload: dict = {}
    i = 0
    while i < len(args):
        tok = args[i]
        if not tok.startswith("--"):
            i += 1
            continue
        key = tok[2:].replace("-", "_")
        # bool flag
        if i + 1 >= len(args) or args[i + 1].startswith("--"):
            payload[key] = True
            i += 1
            continue
        payload[key] = args[i + 1]
        i += 2
    return payload


class AgentHandler(BaseHTTPRequestHandler):
    def _send_json(self, code: int, body: dict):
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {"ok": True, "service": "academic-data-hunter-agent-hub"})
            return
        self._send_json(404, {"ok": False, "error": "not found"})

    def do_POST(self):
        try:
            payload = self._read_json()
        except Exception as e:
            self._send_json(400, {"ok": False, "error": f"invalid json: {e}"})
            return

        if self.path == "/run-round":
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
                    "agent_cmd",
                    "validate_cmd",
                    "report",
                ],
            )
            res = run_script("run_auto_rounds.py", args)
            self._send_json(200 if res["ok"] else 500, res)
            return

        if self.path == "/plan-workflow":
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
            res = run_plan_then_auto(payload)
            self._send_json(200 if res.get("ok") else 500, res)
            return

        if self.path == "/qc-case01":
            args = payload_to_args(payload, ["no_strict_c_cross_check"])
            res = run_script("cases/case01-nev-carbon/scripts/qc_case01.py", args)
            self._send_json(200 if res["ok"] else 500, res)
            return

        self._send_json(404, {"ok": False, "error": "not found"})


def serve(host: str, port: int):
    server = ThreadingHTTPServer((host, port), AgentHandler)
    logging.info("Agent API running at http://%s:%s", host, port)
    logging.info(
        "Endpoints: GET /health, POST /run-round, /validate-round, "
        "/auto-rounds, /plan-workflow, /plan-auto-rounds, /qc-case01"
    )
    server.serve_forever()


def chat():
    logging.info("Academic Data Hunter Interactive Agent")
    logging.info(
        "commands: run_round ..., validate_round ..., auto_rounds ..., "
        "plan_workflow ..., plan_auto_rounds ..., qc_case01, exit"
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
            logging.info("  validate_round --data ... --registry ... --variable charging --value-col ... --check-unit 台")
            logging.info("  auto_rounds --data ... --value-col ... --year-start 2017 --year-end 2023")
            logging.info("  plan_workflow --spec-file templates/research-spec-template.json")
            logging.info("  plan_auto_rounds --spec-file ... --data ... --value-col ... --year-start ... --year-end ...")
            logging.info("  qc_case01")
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
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    parser = argparse.ArgumentParser(description="Hybrid Agent Hub")
    sub = parser.add_subparsers(dest="mode", required=True)

    p_serve = sub.add_parser("serve", help="启动API服务")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8787)

    sub.add_parser("chat", help="启动交互式模式")

    args = parser.parse_args()
    if args.mode == "serve":
        serve(args.host, args.port)
    elif args.mode == "chat":
        chat()


if __name__ == "__main__":
    main()
