# 🎯 Academic Data Hunter

> Provenance-first infrastructure for auditable research data agents  
> 面向高可信研究场景的可审计数据 Agent 基础设施

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP Server](https://img.shields.io/badge/MCP-local%20stdio-blue)](docs/mcp-server.md)
[![Evidence Pack](https://img.shields.io/badge/Delivery-Evidence%20Pack-success)](docs/evidence-pack.md)
[![Benchmark Eval](https://img.shields.io/badge/Reliability-Benchmark%20Eval-purple)](docs/benchmark-evals.md)

## TL;DR

If you are building research agents, this repo gives you the layers that most demos skip:

- **collection workflow**
- **source registry**
- **evidence pack**
- **benchmark / eval**
- **MCP tool surface**

In other words:

> **it helps agents deliver auditable datasets, not just plausible answers.**

## 这是什么？

`academic-data-hunter` 不是“又一个通用 Agent 框架”。

它更适合被理解为：

> **让研究型 Agent 交付“可审计数据资产”而不是“不可验证答案”的工作流基础设施。**

给定一个研究任务，本项目关注的是整条高可信交付链路：

```text
task spec → next-round task → data collection → validation/QC → source registry → evidence pack
```

你最终拿到的不只是一个 CSV，还可以拿到：

- ✅ **dataset**：可继续分析/建模的数据表
- ✅ **source registry**：来源台账
- ✅ **validation result**：一致性与字段完整性检查
- ✅ **evidence pack**：可复核、可交接、可答辩的交付包

## Quick Proof

### Real Case01 benchmark result

From a real run on `cases/case01-nev-carbon`:

| Metric | Value |
|---|---:|
| fill rate | 40.95 |
| provenance completeness | 100.00 |
| registry match rate | 100.00 |
| C-level cross-check rate | 100.00 |
| source quality score | 59.53 |
| overall score | 73.26 |

See:

- [Showcase](docs/showcase.md)
- [Benchmark / Eval](docs/benchmark-evals.md)
- [Why this is not just another agent framework](docs/why-not-just-another-agent-framework.md)

## 为什么需要这个项目？

无论是数学建模、统计建模、论文写作、政策研究还是咨询分析，
**搜集高质量、可追溯、可复核的数据**往往是最耗时也最容易出错的环节。

本项目提供：

- 🔧 **可复用的搜集模板** — 给 AI Agent（Codex / Claude / ChatGPT）的标准化任务文档
- 📋 **完整案例库** — 每个案例包含搜集过程、数据、来源台账和可复现命令
- 🤖 **人机协作工作流** — AI 搜索 + 人工审核 + 自动校验 的最佳实践
- 🧾 **Evidence Pack 交付物** — 把数据、来源与证据组织成可交接的 bundle
- ✅ **研究级可审计** — 每条数据可追溯到来源 URL，经得起答辩、复核与复现

## 适合谁用？

- 需要官方/半官方数据的研究者、竞赛队伍、RA
- 做中文公开数据研究的分析师
- 想给自己的 research agent 接上“高可信数据层”的开发者

## 快速上手（推荐 4 步）

### 1️⃣ 选任务模板
```bash
cp templates/task-spec-template.md my-task.md
```
编辑 `my-task.md`，填入你要搜集的变量名、单位、口径、搜索关键词。

### 2️⃣ 让 Agent 执行搜集
将 `my-task.md` 的内容复制粘贴给 Codex / Claude / ChatGPT，让它按模板执行搜集。

### 3️⃣ 做 QC / 验证
```bash
python tools/qc_checker.py data/my-data.csv
python tools/panel_merger.py --base panel.csv --new data/my-data.csv --on province,year
```

或者使用回合化验证：

```bash
python scripts/validate_round.py ^
  --data cases/case01-nev-carbon/data/charging_piles_by_province.csv ^
  --registry cases/case01-nev-carbon/data/source_registry.csv ^
  --variable charging ^
  --value-col public_charging_piles ^
  --check-unit 台
```

### 4️⃣ 导出 Evidence Pack

```bash
python scripts/export_evidence_pack.py ^
  --data cases/case01-nev-carbon/data/charging_piles_by_province.csv ^
  --registry cases/case01-nev-carbon/data/source_registry.csv ^
  --variable charging ^
  --value-col public_charging_piles ^
  --output-dir tmp/evidence-pack/case01-charging
```

默认会生成：

```text
tmp/evidence-pack/case01-charging/
  manifest.json
  dataset.csv
  source_registry.csv
  evidence_records.jsonl
  README.md
```

### 5️⃣ 跑 Benchmark / Eval

```bash
python scripts/run_benchmark_eval.py ^
  --data cases/case01-nev-carbon/data/charging_piles_by_province.csv ^
  --registry cases/case01-nev-carbon/data/source_registry.csv ^
  --variable charging ^
  --value-col public_charging_piles ^
  --year-start 2017 ^
  --year-end 2023 ^
  --output-json tmp/benchmark/case01-charging.json ^
  --output-md tmp/benchmark/case01-charging.md
```

这个报告会给你：

- fill rate
- provenance completeness
- registry match rate
- C 级来源 cross-check rate
- source quality score
- overall score（0-100）

## 为什么不把它做成通用 Agent 框架？

因为这个仓库最强的不是“聊天壳子”或“通用编排”，而是：

- **来源分级**
- **口径约束**
- **QC 与一致性校验**
- **可复现交付**
- **案例资产**

这也是研究场景里最难被替代的部分。

如果你想快速看差异化叙事，直接看：

- [Showcase](docs/showcase.md)
- [Why this is not just another agent framework](docs/why-not-just-another-agent-framework.md)

## Codex Agent 回合化用法（推荐）

先自动生成“下一轮缺口任务”：

```bash
python scripts/run_round.py \
  --data cases/case01-nev-carbon/data/charging_piles_by_province.csv \
  --value-col public_charging_piles \
  --keyword-name 公共充电桩 \
  --keyword-template1 "{省名} {keyword_name} {year} 保有量 台" \
  --keyword-template2 "{省名} {keyword_name} {year} 截至 台" \
  --year-start 2017 \
  --year-end 2023 \
  --top-years 2 \
  --output cases/case01-nev-carbon/next-round-task.md
```

把 `next-round-task.md` 发给 Agent 执行后，回到仓库做一致性校验：

```bash
python scripts/validate_round.py \
  --data cases/case01-nev-carbon/data/charging_piles_by_province.csv \
  --registry cases/case01-nev-carbon/data/source_registry.csv \
  --variable charging \
  --value-col public_charging_piles \
  --check-unit 台
# 若要开启严格审计（C级必须有cross_check_url），追加:
# --strict-c-cross-check
```

Case01 可直接一键执行完整QC：

```bash
python cases/case01-nev-carbon/scripts/qc_case01.py
```

## 自动多轮调度（可接任意Agent）

先跑 dry-run（只出任务与评估报告）：

```bash
python scripts/run_auto_rounds.py \
  --data cases/case01-nev-carbon/data/charging_piles_by_province.csv \
  --value-col public_charging_piles \
  --year-start 2017 \
  --year-end 2023
# 默认输出：
# - 与 --data 同目录的 next-round-task.md
# - 与 --data 同目录的 auto-round-report.md
```

接入 Agent 后，可用命令模板自动循环多轮：

```bash
python scripts/run_auto_rounds.py \
  --data cases/case01-nev-carbon/data/charging_piles_by_province.csv \
  --value-col public_charging_piles \
  --year-start 2017 \
  --year-end 2023 \
  --agent-cmd "your_agent_runner --task {task_file}" \
  --validate-cmd "python scripts/validate_round.py --data {data} --registry cases/case01-nev-carbon/data/source_registry.csv --variable charging --value-col public_charging_piles --check-unit 台 --strict-c-cross-check"
```

## Hybrid Agent（API + 交互）

启动 API 进程：

```bash
python scripts/agent_hub.py serve --host 127.0.0.1 --port 8787 --api-key your_dev_key
# 默认后端为 FastAPI（可通过 ADH_AGENT_HUB_BACKEND=legacy 切回旧实现）
# OpenAPI 文档： http://127.0.0.1:8787/docs
```

Planner 端点（借鉴 GPT-Researcher 路由）：

```bash
curl -X POST http://127.0.0.1:8787/plan-workflow ^
  -H "Authorization: Bearer your_dev_key" ^
  -H "Content-Type: application/json" ^
  -d "{\"spec_file\":\"templates/research-spec-template.json\"}"
```

一体化端点（先 Planner，再 Auto Rounds）：

```bash
curl -X POST http://127.0.0.1:8787/plan-auto-rounds ^
  -H "Authorization: Bearer your_dev_key" ^
  -H "Content-Type: application/json" ^
  -d "{\"spec_file\":\"templates/research-spec-template.json\",\"data\":\"cases/case01-nev-carbon/data/charging_piles_by_province.csv\",\"value_col\":\"public_charging_piles\",\"year_start\":2017,\"year_end\":2023}"
```

Evidence Pack 导出端点：

```bash
curl -X POST http://127.0.0.1:8787/export-evidence-pack ^
  -H "Authorization: Bearer your_dev_key" ^
  -H "Content-Type: application/json" ^
  -d "{\"data\":\"cases/case01-nev-carbon/data/charging_piles_by_province.csv\",\"registry\":\"cases/case01-nev-carbon/data/source_registry.csv\",\"output_dir\":\"tmp/evidence-pack/case01-api\",\"variable\":\"charging\",\"value_col\":\"public_charging_piles\"}"
```

Benchmark / Eval 端点：

```bash
curl -X POST http://127.0.0.1:8787/benchmark-eval ^
  -H "Authorization: Bearer your_dev_key" ^
  -H "Content-Type: application/json" ^
  -d "{\"data\":\"cases/case01-nev-carbon/data/charging_piles_by_province.csv\",\"registry\":\"cases/case01-nev-carbon/data/source_registry.csv\",\"output_json\":\"tmp/benchmark/case01-api.json\",\"output_md\":\"tmp/benchmark/case01-api.md\",\"variable\":\"charging\",\"value_col\":\"public_charging_piles\",\"year_start\":2017,\"year_end\":2023}"
```

## MCP Server（最小版）

现在仓库内置了一个本地 stdio MCP server，可把核心能力直接暴露给外部 agent 客户端：

- `run_round`
- `validate_round`
- `export_evidence_pack`
- `benchmark_eval`

启动方式：

```bash
python scripts/mcp_server.py
```

Codex 配置示例见：

- [docs/mcp-server.md](docs/mcp-server.md)
- [templates/mcp-servers.example.toml](templates/mcp-servers.example.toml)

若请求参数缺失，API 将返回 `400`，并在响应中附带：
- `stage: "input_validation"`
- `error_code: "missing_required_fields"`
- `missing_fields: [...]`

Docker 一键启动 Agent Hub：

```bash
# 先配置 API Key（可复制 .env.example 为 .env）
# AGENT_HUB_API_KEY=your_strong_key
docker compose up -d --build
# 默认映射 http://127.0.0.1:8787
# 使用环境变量 AGENT_HUB_API_KEY（不再在 compose 明文硬编码）
# 也可通过 ADH_* 环境变量调整抓取超时/缓存与 Agent Hub 默认端口
# 设置 ADH_LOG_JSON=1 可输出结构化 JSON 日志（便于 ELK/Grafana）
# 设置 ADH_FETCH_SSL_VERIFY=0 可临时关闭异步抓取的 SSL 验证（默认开启）
# 设置 ADH_AGENT_HUB_SCRIPT_TIMEOUT_SEC=900 可放宽 Hub 子进程执行超时（默认 600 秒）
```

启动交互式模式：

```bash
python scripts/agent_hub.py chat
```

## 项目结构

```
├── docs/           # 方法论、定位、roadmap、evidence-pack 说明
├── templates/      # 可复用模板（任务文档、进度汇报、来源台账、manifest 示例）
├── tools/          # 通用工具（QC检查、面板合并、省份映射、抓取/抽取）
├── scripts/        # 回合化脚手架、验证、自动调度、evidence-pack 导出、Agent Hub
├── cases/          # 案例库
│   ├── case01-nev-carbon/  # 案例1（含 scripts/）
│   ├── case02-nev-emission-controls/  # 案例2（含 scripts/）
│   └── case03-population-10y/  # 案例3（含 scripts/）
└── .agent/         # AI Agent 工作流配置
```

## 案例列表

| # | 案例 | 变量 | 面板规模 | 状态 |
|---|------|------|----------|------|
| 01 | [新能源车碳减排](cases/case01-nev-carbon/) | 充电桩、公交车、发电量、燃油消耗等17个 | 30省×2012-2023 | ✅ 完成 |
| 02 | [NEV+交通碳排放控制变量](cases/case02-nev-emission-controls/) | 交通碳排放估算、NEV、人均GDP、城镇化率、客/货运周转量、公路里程、第三产业占比 | 30省×2012-2023 | ✅ 完成 |
| 03 | [全国近十年人口](cases/case03-population-10y/) | 年末常住人口（万人） | 30省×2015-2024 | ✅ 完成 |

### Case02 快速命令

```bash
python cases/case02-nev-emission-controls/scripts/collect_case02.py
python cases/case02-nev-emission-controls/scripts/export_case02_xlsx.py
python cases/case02-nev-emission-controls/scripts/qc_case02.py
python cases/case02-nev-emission-controls/scripts/compare_case02_with_delivery.py
python cases/case02-nev-emission-controls/scripts/discover_case02_nev_camoufox.py --resume --run-mode headless --output cases/case02-nev-emission-controls/tmp/camoufox_missing7_v2.json --engines google,bing,sogou,360 --max-pages 30 --fetch-workers 8
python cases/case02-nev-emission-controls/scripts/report_case02_nev_strict_status.py --candidates cases/case02-nev-emission-controls/tmp/camoufox_missing7_v2.json --output cases/case02-nev-emission-controls/strict-nev-status.md
python cases/case02-nev-emission-controls/scripts/run_case02_nev_strict_autopilot.py --rounds 3 --run-mode headless --max-pages 30 --max-fetch-pages 20 --fetch-workers 8 --engines google,tavily,bing,sogou,360 --skip-collect
python scripts/organize_tmp_files.py
python scripts/run_round.py --data cases/case02-nev-emission-controls/data/panel_case02_30prov_2012_2023.csv --value-col transport_co2_est_10k_ton --keyword-name 交通碳排放估算 --keyword-template1 "{省名} {keyword_name} {year}" --keyword-template2 "{省名} 交通运输 二氧化碳排放 {year}" --year-start 2012 --year-end 2023 --top-years 2 --output cases/case02-nev-emission-controls/next-round-task.md
python scripts/run_auto_rounds.py --data cases/case02-nev-emission-controls/data/panel_case02_30prov_2012_2023.csv --value-col transport_co2_est_10k_ton --year-start 2012 --year-end 2023 --max-rounds 2 --task-output cases/case02-nev-emission-controls/next-round-task.md --report cases/case02-nev-emission-controls/auto-round-report.md
```

可选“快速参数”（降低等待与超时）：
`--delay-min-ms 300 --delay-max-ms 700 --query-timeout-ms 18000 --request-timeout-sec 12`

可选“增强搜索参数”（提高召回/并发）：
`--engine-mode merge --province-workers 2 --fetch-workers 12 --fetch-mode async --per-domain-cap 4`
（如使用 `--fetch-mode async`，建议先安装 `aiohttp` 或 `pip install -e .[async]`）

### 快速新建“人口”案例

```bash
python cases/case03-population-10y/scripts/init_population_case.py --case-dir cases/case03-population-10y --year-start 2015 --year-end 2024
```

> 说明：`run_case02_nev_strict_autopilot.py` 已默认接入处理层（`process_web_data_pipeline.py`），
> 每轮会自动生成 `processed_roundN/`（markdown归档 + schema抽取）。  
> 如需仅搜索可加：`--skip-processing`  
> 如需忽略历史续跑结果并清空 autopilot 旧产物：`--fresh-output --force`

### 高级用户：Google + Tavily 混合搜索

```bash
# 推荐：把 Tavily Key 放环境变量
set TAVILY_API_KEY=your_key_here

# 用配置文件管理高级参数
python cases/case02-nev-emission-controls/scripts/discover_case02_nev_camoufox.py \
  --config templates/advanced-search-config.example.toml \
  --schema-file templates/candidate-extractor-schema.example.json \
  --resume \
  --output cases/case02-nev-emission-controls/tmp/camoufox_missing7_advanced.json
```

### 高级用户：MCP（Tavily / Exa）检查

```bash
python scripts/check_mcp_servers.py
# 可自定义必需项：
# python scripts/check_mcp_servers.py --required tavily-proxy,exa-proxy
```

> 说明：MCP 属于 Agent 运行层能力；本仓库脚本层可配多引擎，MCP 由你本机 `~/.codex/config.toml` 管理。
> 可参考模板：`templates/mcp-servers.example.toml`

### 借鉴 ScrapeGraphAI 的数据处理分层（markdown + schema抽取）

```bash
# 1) 先拿 discover 候选JSON
# 2) 再做内容归档与结构化抽取
python scripts/process_web_data_pipeline.py \
  --input-json cases/case02-nev-emission-controls/tmp/camoufox_missing7_v2.json \
  --schema-file templates/extraction-schema-template.json \
  --output-dir cases/case02-nev-emission-controls/tmp/processed \
  --mode both
```

### 借鉴 GPT-Researcher 的 Planner 路由（任务拆解）

```bash
python scripts/plan_research_workflow.py \
  --spec-file templates/research-spec-template.json
```

会自动生成：
- `templates/research-spec-template.plan.json`
- `templates/research-spec-template.plan.md`

## 核心方法论

详见 [docs/methodology.md](docs/methodology.md)

定位说明见 [docs/positioning.md](docs/positioning.md)

使用场景见 [docs/use-cases.md](docs/use-cases.md)

Evidence Pack 说明见 [docs/evidence-pack.md](docs/evidence-pack.md)

Benchmark / Eval 说明见 [docs/benchmark-evals.md](docs/benchmark-evals.md)

MCP Server 说明见 [docs/mcp-server.md](docs/mcp-server.md)

Showcase 说明见 [docs/showcase.md](docs/showcase.md)

差异化说明见 [docs/why-not-just-another-agent-framework.md](docs/why-not-just-another-agent-framework.md)

路线图见 [docs/roadmap.md](docs/roadmap.md)

Codex 协作执行详见 [docs/codex-agent-playbook.md](docs/codex-agent-playbook.md)

架构总览详见 [docs/architecture.md](docs/architecture.md)

```
定义变量与口径 → API自动化抓取 → Web搜索补缺 → 人机协作深挖 → QC入库合并
```

## 依赖与环境管理

- 运行时依赖以 `pyproject.toml` 的 `[project].dependencies` 为准
- `requirements.txt` 与上述依赖保持同步（可用 `python scripts/check_dependency_sync.py` 校验）
- 文档命令可用 `python scripts/check_docs_command_paths.py` 做路径一致性校验
- 安装与复现实验环境优先使用 `requirements-lock.txt`（Python 3.11 锁定）
- 审核阶段建议运行 `python scripts/run_review_gate.py` 生成可复现验证报告（默认输出到 `tmp/review/`）
- 变更过多时可运行 `python scripts/summarize_workspace_changes.py` 生成工作区变更分组摘要（默认输出到 `tmp/review/`）

## 来源分级规则

| 等级 | 来源类型 | 入库条件 |
|------|---------|---------|
| **A** | 政府官网、统计年鉴 | 直接入库 |
| **B** | 行业协会官方发布 | 直接入库 |
| **C** | 媒体、研究机构 | 需标注 + 交叉核验 |

## 贡献

欢迎提交新案例！请参考 [cases/case01-nev-carbon/](cases/case01-nev-carbon/) 的结构：

1. Fork 本仓库
2. 在 `cases/` 下创建新目录 `caseXX-你的主题/`
3. 包含：`README.md`、`task-spec.md`、`data/`、`scripts/`
4. 提交 PR

更完整的协作规范见 [CONTRIBUTING.md](CONTRIBUTING.md)。

第二用户可复现性检查模板见 [docs/first-user-validation.md](docs/first-user-validation.md)。

## License

MIT
