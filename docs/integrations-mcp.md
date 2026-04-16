# MCP 集成

项目提供本地 stdio MCP server，让外部 MCP 客户端可以直接调用 workflow 的核心工具。

## 当前开放的工具

- `run_round`
- `validate_round`
- `export_evidence_pack`
- `benchmark_eval`

## 本地启动

```bash
python scripts/mcp_server.py
```

## 典型用途

- 把 workflow 接到 Agent
- 用 MCP 统一调度数据校验与交付
- 用外部客户端直接调用证据与评估工具
