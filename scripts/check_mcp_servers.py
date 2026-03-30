#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 Codex 配置中的 MCP 搜索服务器（如 tavily / exa）是否已配置。
"""

from __future__ import annotations

import argparse
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
    args = parse_args()
    cfg_path = Path(args.config)
    if not cfg_path.exists():
        print(f"[ERR] config not found: {cfg_path}")
        raise SystemExit(1)

    data = tomllib.loads(cfg_path.read_text(encoding="utf-8"))
    mcp = data.get("mcp_servers", {})
    if not isinstance(mcp, dict):
        print("[ERR] mcp_servers section missing")
        raise SystemExit(1)

    required = [x.strip() for x in args.required.split(",") if x.strip()]
    found = [x for x in required if x in mcp]
    missing = [x for x in required if x not in mcp]

    print(f"[INFO] config: {cfg_path}")
    print(f"[INFO] mcp servers total: {len(mcp)}")
    print(f"[OK] found: {', '.join(found) if found else '-'}")
    print(f"[WARN] missing: {', '.join(missing) if missing else '-'}")

    if missing:
        print("\n# exa 示例（按实际服务地址/凭证替换）")
        print("[mcp_servers.exa-proxy]")
        print('command = "npx"')
        print('args = ["-y", "mcp-remote", "https://<your-exa-mcp-endpoint>/mcp", "--header", "Authorization: Bearer <TOKEN>"]')


if __name__ == "__main__":
    main()

