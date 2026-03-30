# First User Validation (Second-user Dry Run)

目的：验证仓库文档是否能让**非作者**从零完成一次可复现实验。

## 验证范围

- 环境准备（依赖安装）
- 基础检查（lint / mypy / pytest）
- 跑通一个最小工作流（run_round -> validate_round）
- Agent Hub API 的鉴权与基本路由

## 执行记录模板

| 项目 | 结果 | 备注 |
|---|---|---|
| clone 仓库 | ☐/☑ | |
| 安装依赖（requirements-lock） | ☐/☑ | |
| `ruff check .` | ☐/☑ | |
| `mypy tools/` | ☐/☑ | |
| `pytest -q tests/` | ☐/☑ | |
| `python scripts/run_round.py --help` | ☐/☑ | |
| `python scripts/validate_round.py --help` | ☐/☑ | |
| `python scripts/agent_hub.py serve --api-key ...` | ☐/☑ | |
| `GET /health`（带 Bearer） | ☐/☑ | |

## 建议执行步骤

1. 按 README 完成依赖安装。  
2. 运行 CI 同款本地检查：
   - `python -m ruff check .`
   - `python -m mypy tools/ --ignore-missing-imports`
   - `python -m pytest -q tests/`
3. 启动 API：
   - `python scripts/agent_hub.py serve --host 127.0.0.1 --port 8787 --api-key dev_key`
4. 验证接口：
   - `curl -H "Authorization: Bearer dev_key" http://127.0.0.1:8787/health`

## 常见卡点（持续更新）

- Windows PowerShell 下引号转义导致 curl JSON 失败
- 本地 Python 版本与 lockfile 目标版本不一致
- 未设置 `Authorization` 请求头导致 401

## 反馈闭环

请把第二用户遇到的问题回填到：

- `README.md`（启动/命令示例）
- `CONTRIBUTING.md`（提交流程/测试流程）
- 本文档（卡点与修复记录）
