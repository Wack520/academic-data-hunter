# 🎯 Academic Data Hunter

> 面向学术竞赛的数据搜集方法论工具包 — 用 AI Agent 高效搜集可审计的官方数据

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 为什么需要这个项目？

参加统计建模、数学建模、数据分析竞赛时，**搜集高质量、可追溯的官方数据**往往是最耗时的环节。

本项目提供：

- 🔧 **可复用的搜集模板** — 给 AI Agent（Codex / Claude / ChatGPT）的标准化任务文档
- 📋 **完整案例库** — 每个案例包含搜集过程、数据、来源台账，可直接参考
- 🤖 **人机协作工作流** — AI搜索 + 人工审核 的最佳实践
- ✅ **学术可审计** — 每条数据可追溯到来源URL，经得起答辩质疑

## 快速上手（3步）

### 1️⃣ 选模板
```bash
cp templates/task-spec-template.md my-task.md
```
编辑 `my-task.md`，填入你要搜集的变量名、单位、口径、搜索关键词。

### 2️⃣ 给 AI Agent
将 `my-task.md` 的内容复制粘贴给 Codex / Claude / ChatGPT，让它按模板执行搜集。

### 3️⃣ QC 入库
```bash
python tools/qc_checker.py data/my-data.csv
python tools/panel_merger.py --base panel.csv --new data/my-data.csv --on province,year
```

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

Docker 一键启动 Agent Hub：

```bash
docker compose up -d --build
# 默认映射 http://127.0.0.1:8787
# 默认 key: dev-change-me（可在 docker-compose.yml 中修改）
```

启动交互式模式：

```bash
python scripts/agent_hub.py chat
```

## 项目结构

```
├── docs/           # 方法论文档
├── templates/      # 可复用模板（任务文档、进度汇报、来源台账）
├── tools/          # 通用工具（QC检查、面板合并、省份映射）
├── scripts/        # 回合化脚手架（任务生成、结果校验、自动调度）
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
| 03 | [全国近十年人口](cases/case03-population-10y/) | 年末常住人口（万人） | 30省×2015-2024 | 🚧 初始化 |

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
`--engine-mode merge --province-workers 2 --fetch-workers 12 --per-domain-cap 4`

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

Codex 协作执行详见 [docs/codex-agent-playbook.md](docs/codex-agent-playbook.md)

架构总览详见 [docs/architecture.md](docs/architecture.md)

```
定义变量与口径 → API自动化抓取 → Web搜索补缺 → 人机协作深挖 → QC入库合并
```

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

## License

MIT
