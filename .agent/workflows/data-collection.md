---
description: 使用AI Agent搜集学术研究数据的标准工作流
---

# 数据搜集工作流

// turbo-all

## 1. 准备任务文档

复制模板并填写变量信息：

```bash
cp templates/task-spec-template.md my-task.md
```

编辑 `my-task.md`，替换所有 `{占位符}`：
- `{变量中文名}` → 如"公共充电桩"
- `{variable_name}` → 如"public_charging_piles"
- `{单位}` → 如"台"
- `{起始年份}` / `{结束年份}` → 如"2016" / "2023"

## 2. API/数据库优先搜集

如果变量可通过API获取，优先执行你项目内已有抓取脚本（本仓库默认不内置统一 `stats_api_fetcher.py`）：
```bash
# 示例（按你的脚本实际参数替换）
python tools/<your_api_script>.py --indicator {指标ID} --years {范围}
```

如果需要下载数据库文件，手动下载后放到 `cases/caseXX/data/`，并记录来源台账。

## 3. 给 AI Agent（Codex）执行深度搜索

将任务文档内容发送给 Codex：
```
请阅读以下任务文档并按规范执行数据搜集：
[粘贴 my-task.md 内容]
```

## 4. 审查结果并补充

收到 Codex 结果后：
```bash
python tools/qc_checker.py data/output.csv --key province,year --required source_url
```

如有缺口，给 Codex 补充任务（使用 `templates/progress-report-template.md` 格式汇报进度）。

## 5. 合并到面板

```bash
python tools/panel_merger.py \
    --base data/panel.csv \
    --new data/output.csv \
    --on province,year \
    --map-province full
```

## 6. 最终QC

```bash
python tools/qc_checker.py data/panel.csv --key province,year
```

确认：
- 行数不变
- 新列非空数与源表一致
- 无重复键

## 7. Codex Agent 回合制（推荐）

使用脚手架生成“下一轮缺口任务”，让 Codex 按轮执行：

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

每轮完成后做一致性验证：

```bash
python scripts/validate_round.py \
  --data cases/case01-nev-carbon/data/charging_piles_by_province.csv \
  --registry cases/case01-nev-carbon/data/source_registry.csv \
  --variable charging \
  --value-col public_charging_piles \
  --check-unit 台
# 需要严格审计时追加:
# --strict-c-cross-check
```

Case01 一键QC：

```bash
python cases/case01-nev-carbon/scripts/qc_case01.py
```

## 8. 自动多轮调度（可选）

```bash
python scripts/run_auto_rounds.py \
  --data cases/case01-nev-carbon/data/charging_piles_by_province.csv \
  --value-col public_charging_piles \
  --year-start 2017 \
  --year-end 2023 \
  --agent-cmd "your_agent_runner --task {task_file}" \
  --validate-cmd "python scripts/validate_round.py --data {data} --registry cases/case01-nev-carbon/data/source_registry.csv --variable charging --value-col public_charging_piles --check-unit 台 --strict-c-cross-check"
```

## 9. Hybrid Agent 入口（API + 交互）

```bash
# API服务
python scripts/agent_hub.py serve --host 127.0.0.1 --port 8787

# 交互式REPL
python scripts/agent_hub.py chat
```

API 新增：`POST /plan-workflow`（输入 `spec_file`，输出 planner 计划文件）。
API 新增：`POST /plan-auto-rounds`（先规划再自动多轮执行）。

## 10. 高级搜索（多引擎 + Tavily）

```bash
# Windows
set TAVILY_API_KEY=your_key_here

# Google + Tavily + 传统引擎混合
python cases/case02-nev-emission-controls/scripts/discover_case02_nev_camoufox.py \
  --config templates/advanced-search-config.example.toml \
  --engines google,tavily,bing,sogou,360 \
  --output cases/case02-nev-emission-controls/tmp/camoufox_missing7_advanced.json
```

检查 MCP 搜索服务（Tavily / Exa）是否在 Codex 配置中生效：

```bash
python scripts/check_mcp_servers.py --required tavily-proxy,exa-proxy
```

## 11. 数据处理分层（借鉴 ScrapeGraphAI）

```bash
python scripts/process_web_data_pipeline.py \
  --input-json cases/case02-nev-emission-controls/tmp/camoufox_missing7_v2.json \
  --schema-file templates/extraction-schema-template.json \
  --output-dir cases/case02-nev-emission-controls/tmp/processed \
  --mode both
```

自动续跑已内置该处理层（默认开启）：

```bash
python cases/case02-nev-emission-controls/scripts/run_case02_nev_strict_autopilot.py --rounds 3 --skip-collect
# 若只要搜索，不跑处理层：
# --skip-processing
```

## 12. Planner 路由（借鉴 GPT-Researcher）

```bash
python scripts/plan_research_workflow.py --spec-file templates/research-spec-template.json
```

Planner 会把变量自动路由到：
- API执行器
- 浏览器/搜索执行器
- 文档/表格执行器
