# MCP Server

`academic-data-hunter` now ships a minimal local MCP server over **stdio**.

## Why it exists

This turns the project from “a repository with scripts” into “a research-data tool layer” that external agent clients can call directly.

## Current tools

- `run_round`
- `validate_round`
- `export_evidence_pack`
- `benchmark_eval`

## Start locally

```bash
python scripts/mcp_server.py
```

The server speaks line-delimited JSON-RPC over stdio and supports:

- `initialize`
- `tools/list`
- `tools/call`
- `ping`
- `shutdown`
- `exit`

## 本地客户端配置示例（以 Codex 为例）

把下面片段加入本地 `~/.codex/config.toml`：

```toml
[mcp_servers.academic-data-hunter]
command = "python"
args = ["<PROJECT_ROOT>/scripts/mcp_server.py"]
```

把 `<PROJECT_ROOT>` 替换成你的仓库绝对路径后，即可通过 MCP 直接调用项目工具。

## Example tool call target

The most useful first calls are:

- `export_evidence_pack`
- `benchmark_eval`

These are the best demo surfaces for auditable dataset delivery.
