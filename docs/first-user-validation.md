# 首个外部用户验证

这份文档用于检查：一个**非作者**是否能从零跑通仓库里的最小工作流。

## 验证范围

- 环境准备
- 基础检查（lint / mypy / pytest）
- 跑通最小流程（`run_round -> validate_round`）
- Agent Hub API 基本启动与鉴权

## 建议检查项

| 项目 | 结果 | 备注 |
|---|---|---|
| clone 仓库 | ☐/☑ | |
| 安装依赖 | ☐/☑ | |
| `ruff check .` | ☐/☑ | |
| `mypy tools/` | ☐/☑ | |
| `pytest -q tests/` | ☐/☑ | |
| `python scripts/run_round.py --help` | ☐/☑ | |
| `python scripts/validate_round.py --help` | ☐/☑ | |
| `python scripts/agent_hub.py serve --api-key ...` | ☐/☑ | |
| `GET /health`（带 Bearer） | ☐/☑ | |

## 推荐执行步骤

1. 按 README 安装依赖。  
2. 运行本地检查：
   - `python -m ruff check .`
   - `python -m mypy tools/ --ignore-missing-imports`
   - `python -m pytest -q tests/`
3. 启动 API：
   - `python scripts/agent_hub.py serve --host 127.0.0.1 --port 8787 --api-key dev_key`
4. 验证接口：
   - `curl -H "Authorization: Bearer dev_key" http://127.0.0.1:8787/health`

## 一键复现

```bash
python scripts/run_review_gate.py
```

默认生成：

- `tmp/review/review-gate-latest.json`
- `tmp/review/review-gate-latest.md`

## 常见卡点

- Windows PowerShell 下引号转义问题
- 本地 Python 版本与 lockfile 不一致
- 请求缺少 `Authorization` 头导致 401
