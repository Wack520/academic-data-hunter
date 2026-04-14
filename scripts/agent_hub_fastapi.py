"""
FastAPI backend for Hybrid Agent Hub API.

This module mirrors the legacy endpoints in scripts/agent_hub.py while
providing ASGI support and OpenAPI schema generation.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import secrets
from collections.abc import Callable

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

try:
    from scripts.agent_hub_common import (
        missing_required_fields,
        payload_to_args,
        run_plan_then_auto,
        run_script,
    )
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    from agent_hub_common import (
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


def _parse_json_body(raw: bytes) -> dict:
    if not raw:
        return {}
    try:
        value = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise ValueError(f"invalid json: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("invalid json: root must be object")
    return value


def create_app(api_key: str, max_request_body_bytes: int = AGENT_HUB_MAX_REQUEST_BODY_BYTES) -> FastAPI:
    app = FastAPI(title="Academic Data Hunter Agent Hub", version="1.0.0")
    app.state.required_api_key = (api_key or "").strip()
    app.state.max_request_body_bytes = int(max_request_body_bytes)

    @app.middleware("http")
    async def auth_and_size_guard(request: Request, call_next: Callable):  # type: ignore[no-redef]
        required_api_key = str(request.app.state.required_api_key or "")
        if required_api_key:
            auth = (request.headers.get("Authorization") or "").strip()
            if auth != f"Bearer {required_api_key}":
                return JSONResponse(status_code=401, content={"ok": False, "error": "unauthorized"})

        if request.method in {"POST", "PUT", "PATCH"}:
            content_length_header = request.headers.get("Content-Length", "")
            if content_length_header:
                try:
                    content_length = int(content_length_header)
                except ValueError:
                    return JSONResponse(
                        status_code=400, content={"ok": False, "error": "invalid json: invalid Content-Length"}
                    )
                if content_length > request.app.state.max_request_body_bytes:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "ok": False,
                            "error": (
                                f"invalid json: payload too large: {content_length} bytes "
                                f"(max {request.app.state.max_request_body_bytes})"
                            ),
                        },
                    )

            raw = await request.body()
            if len(raw) > request.app.state.max_request_body_bytes:
                return JSONResponse(
                    status_code=400,
                    content={
                        "ok": False,
                        "error": (
                            f"invalid json: payload too large: {len(raw)} bytes "
                            f"(max {request.app.state.max_request_body_bytes})"
                        ),
                    },
                )
            request.state.raw_body = raw

        return await call_next(request)

    async def read_payload(request: Request) -> dict:
        raw = getattr(request.state, "raw_body", b"")
        try:
            return _parse_json_body(raw)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    def ensure_required(payload: dict, required: list[str]) -> None:
        missing = missing_required_fields(payload, required)
        if missing:
            raise HTTPException(
                status_code=400,
                detail={
                    "stage": "input_validation",
                    "error_code": "missing_required_fields",
                    "error": f"missing required fields: {', '.join(missing)}",
                    "missing_fields": missing,
                },
            )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException):  # type: ignore[no-redef]
        if isinstance(exc.detail, str):
            return JSONResponse(status_code=exc.status_code, content={"ok": False, "error": exc.detail})
        if isinstance(exc.detail, dict):
            payload = {"ok": False}
            payload.update(exc.detail)
            return JSONResponse(status_code=exc.status_code, content=payload)
        return JSONResponse(status_code=exc.status_code, content={"ok": False, "error": "http error"})

    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(_: Request, exc: StarletteHTTPException):  # type: ignore[no-redef]
        if exc.status_code == 404:
            return JSONResponse(status_code=404, content={"ok": False, "error": "not found"})
        if isinstance(exc.detail, str):
            return JSONResponse(status_code=exc.status_code, content={"ok": False, "error": exc.detail})
        return JSONResponse(status_code=exc.status_code, content={"ok": False, "error": "http error"})

    @app.get("/health")
    async def health() -> dict:
        return {"ok": True, "service": "academic-data-hunter-agent-hub"}

    @app.post("/run-round")
    async def run_round_endpoint(request: Request):  # type: ignore[no-redef]
        payload = await read_payload(request)
        ensure_required(payload, ["data", "value_col", "year_start", "year_end", "output"])
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
        return JSONResponse(status_code=200 if res["ok"] else 500, content=res)

    @app.post("/validate-round")
    async def validate_round_endpoint(request: Request):  # type: ignore[no-redef]
        payload = await read_payload(request)
        ensure_required(payload, ["data", "registry", "variable"])
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
        return JSONResponse(status_code=200 if res["ok"] else 500, content=res)

    @app.post("/auto-rounds")
    async def auto_rounds_endpoint(request: Request):  # type: ignore[no-redef]
        payload = await read_payload(request)
        ensure_required(payload, ["data", "value_col", "year_start", "year_end"])
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
        return JSONResponse(status_code=200 if res["ok"] else 500, content=res)

    @app.post("/plan-workflow")
    async def plan_workflow_endpoint(request: Request):  # type: ignore[no-redef]
        payload = await read_payload(request)
        ensure_required(payload, ["spec_file"])
        args = payload_to_args(payload, ["spec_file", "out_json", "out_md"])
        res = run_script("plan_research_workflow.py", args)
        return JSONResponse(status_code=200 if res["ok"] else 500, content=res)

    @app.post("/plan-auto-rounds")
    async def plan_auto_rounds_endpoint(request: Request):  # type: ignore[no-redef]
        payload = await read_payload(request)
        ensure_required(payload, ["spec_file", "data", "value_col", "year_start", "year_end"])
        res = run_plan_then_auto(payload)
        stage = (res or {}).get("stage")
        status = 200 if res.get("ok") else (400 if stage == "input_validation" else 500)
        return JSONResponse(status_code=status, content=res)

    @app.post("/qc-case01")
    async def qc_case01_endpoint(request: Request):  # type: ignore[no-redef]
        payload = await read_payload(request)
        args = payload_to_args(payload, ["no_strict_c_cross_check"])
        res = run_script("cases/case01-nev-carbon/scripts/qc_case01.py", args)
        return JSONResponse(status_code=200 if res["ok"] else 500, content=res)

    @app.post("/export-evidence-pack")
    async def export_evidence_pack_endpoint(request: Request):  # type: ignore[no-redef]
        payload = await read_payload(request)
        ensure_required(payload, ["data", "registry", "output_dir"])
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
        return JSONResponse(status_code=200 if res["ok"] else 500, content=res)

    @app.post("/benchmark-eval")
    async def benchmark_eval_endpoint(request: Request):  # type: ignore[no-redef]
        payload = await read_payload(request)
        ensure_required(payload, ["data", "registry", "output_json"])
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
        return JSONResponse(status_code=200 if res["ok"] else 500, content=res)

    return app


def serve(host: str, port: int, api_key: str) -> None:
    required_api_key = (api_key or "").strip()
    if not required_api_key:
        required_api_key = secrets.token_urlsafe(24)
        logging.warning("No --api-key provided, generated ephemeral API key: %s", required_api_key)
    app = create_app(required_api_key, max_request_body_bytes=AGENT_HUB_MAX_REQUEST_BODY_BYTES)
    logging.info("Agent API running at http://%s:%s", host, port)
    logging.info("Auth: enabled (Authorization: Bearer <api-key>)")
    logging.info(
        "Endpoints: GET /health, POST /run-round, /validate-round, "
        "/auto-rounds, /plan-workflow, /plan-auto-rounds, /qc-case01, "
        "/export-evidence-pack, /benchmark-eval"
    )
    uvicorn.run(app, host=host, port=int(port), log_level="info")


def main() -> None:
    configure_logging()
    parser = argparse.ArgumentParser(description="FastAPI Agent Hub")
    parser.add_argument("--host", default=AGENT_HUB_DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=AGENT_HUB_DEFAULT_PORT)
    parser.add_argument(
        "--api-key",
        default=os.environ.get("AGENT_HUB_API_KEY", ""),
        help="API鉴权密钥（请求头需传 Authorization: Bearer <key>）",
    )
    args = parser.parse_args()
    serve(args.host, args.port, args.api_key)


if __name__ == "__main__":
    main()
