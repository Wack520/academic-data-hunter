#!/usr/bin/env python3
"""
检查 Codex 配置中的 MCP 搜索服务器（如 tavily / exa）是否已配置。
"""

from __future__ import annotations

import argparse
import logging
import os
import tomllib
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="检查 MCP 搜索服务器配置")
    p.add_argument(
        "--config",
        default=os.environ.get("CODEX_CONFIG", r"C:\Users\21115\.codex\config.toml"),
        help="Codex config.toml 路径",
    )
    p.add_argument("--required", default="tavily-proxy,exa-proxy", help="必需服务器名，逗号分隔")
    return p.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    args = parse_args()
    cfg_path = Path(args.config)
    if not cfg_path.exists():
        logging.error("config not found: %s", cfg_path)
        raise SystemExit(1)

    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    mcp = data.get("mcp_servers", {})
    if not isinstance(mcp, dict):
        logging.error("mcp_servers section missing")
        raise SystemExit(1)

    required = [x.strip() for x in args.required.split(",") if x.strip()]
    found = [x for x in required if x in mcp]
    missing = [x for x in required if x not in mcp]

    logging.info("config: %s", cfg_path)
    logging.info("mcp servers total: %s", len(mcp))
    logging.info("found: %s", ", ".join(found) if found else "-")
    logging.warning("missing: %s", ", ".join(missing) if missing else "-")

    if missing:
        logging.info("# exa 示例（按实际服务地址/凭证替换）")
        logging.info("[mcp_servers.exa-proxy]")
        logging.info('command = "npx"')
        logging.info(
            'args = ["-y", "mcp-remote", "https://<your-exa-mcp-endpoint>/mcp", "--header", "Authorization: Bearer <TOKEN>"]'
        )


if __name__ == "__main__":
    main()
