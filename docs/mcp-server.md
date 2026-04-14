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

## Codex config example

Add this to your local `~/.codex/config.toml`:

```toml
[mcp_servers.academic-data-hunter]
command = "python"
args = ["D:/Desk/academic-data-hunter/scripts/mcp_server.py"]
```

Then your client can call the project tools directly through MCP.

## Example tool call target

The most useful first calls are:

- `export_evidence_pack`
- `benchmark_eval`

These are the best demo surfaces for auditable dataset delivery.
