# MCP 接入

项目提供一个本地 **stdio MCP server**，让外部 MCP 客户端可以直接调用核心数据交付工具。

## 它能做什么

当前开放的工具有：

- `run_round`
- `validate_round`
- `export_evidence_pack`
- `benchmark_eval`

## 本地启动

```bash
python scripts/mcp_server.py
```

服务通过 stdio 读写 JSON-RPC，适合作为本地研究数据工具层接入。

## 客户端配置示例（以 Codex 为例）

把下面片段加入本地 `~/.codex/config.toml`：

```toml
[mcp_servers.academic-data-hunter]
command = "python"
args = ["<PROJECT_ROOT>/scripts/mcp_server.py"]
```

把 `<PROJECT_ROOT>` 替换成你的仓库绝对路径即可。

## 建议先试的两个工具

- `export_evidence_pack`：看完整交付包
- `benchmark_eval`：看一次数据交付的量化评估结果
