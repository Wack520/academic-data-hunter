# Academic Data Hunter

> 面向研究、竞赛与论文场景的可追溯数据采集与交付工具

[![CI](https://github.com/Wack520/academic-data-hunter/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Wack520/academic-data-hunter/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Evidence Pack](https://img.shields.io/badge/Delivery-Evidence%20Pack-success)](docs/evidence-pack.md)
[![Benchmark Eval](https://img.shields.io/badge/Reliability-Benchmark%20Eval-purple)](docs/benchmark-evals.md)
[![MCP Server](https://img.shields.io/badge/MCP-local%20stdio-blue)](docs/mcp-server.md)

## 这是什么

Academic Data Hunter 用来把“找数据”变成“交付数据”。

围绕一个研究任务，它提供一套可复用流程，帮助你完成：

- **数据采集**：围绕任务模板和案例流程搜集公开数据
- **来源登记**：记录 source registry、来源等级与证据记录
- **质量校验**：做字段完整性、一致性与交叉核验
- **结果交付**：输出数据表、Evidence Pack 与 Benchmark Eval

如果你需要的不是一段回答，而是一份**可继续分析、可回溯来源、可交接复核**的数据资产，这个项目就是为这件事做的。

## 核心能力

### 1. 可追溯的数据采集流程

用统一任务模板组织变量、单位、年份范围、来源口径与搜索关键词，让 Agent 或人工协作按同一规则执行。

### 2. 可复核的交付物

除了数据表，还可以输出：

- `source_registry.csv`
- `evidence_records.jsonl`
- `manifest.json`
- `README.md`

也就是完整的 **Evidence Pack**。

### 3. 可量化的结果评估

通过 **Benchmark Eval** 对交付质量打分，包括：

- 填充率（fill rate）
- 来源完整性（provenance completeness）
- 台账匹配率（registry match rate）
- C级来源交叉核验率（C-level cross-check rate）
- 来源质量分（source quality score）
- 总分（overall score）

## 适合谁用

- 数学建模、统计建模、论文写作中的数据收集场景
- 需要官方 / 半官方来源且必须能追溯出处的研究任务
- 想给自己的 AI Agent 接上“数据层”和“证据层”的开发者

## 快速开始

### 1）准备任务模板

```bash
cp templates/task-spec-template.md my-task.md
```

在 `my-task.md` 中填写变量名、单位、年份范围、口径和搜索关键词。

### 2）做数据校验

```bash
python scripts/validate_round.py ^
  --data cases/case01-nev-carbon/data/charging_piles_by_province.csv ^
  --registry cases/case01-nev-carbon/data/source_registry.csv ^
  --variable charging ^
  --value-col public_charging_piles ^
  --check-unit 台
```

### 3）导出交付包

```bash
python scripts/export_evidence_pack.py ^
  --data cases/case01-nev-carbon/data/charging_piles_by_province.csv ^
  --registry cases/case01-nev-carbon/data/source_registry.csv ^
  --variable charging ^
  --value-col public_charging_piles ^
  --output-dir tmp/evidence-pack/case01-charging
```

### 4）运行评估

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

## 代表案例

| 案例 | 内容 | 规模 | 状态 |
|---|---|---|---|
| [case01-nev-carbon](cases/case01-nev-carbon/) | 新能源车碳减排相关数据 | 30省 × 2012-2023 | ✅ |
| [case02-nev-emission-controls](cases/case02-nev-emission-controls/) | NEV 与交通碳排放控制变量 | 30省 × 2012-2023 | ✅ |
| [case03-population-10y](cases/case03-population-10y/) | 全国近十年人口数据 | 30省 × 2015-2024 | ✅ |

## 一个真实结果

来自 `cases/case01-nev-carbon` 的一次真实评估结果：

| 指标 | 数值 |
|---|---:|
| 填充率 | 40.95 |
| 来源完整性 | 100.00 |
| 台账匹配率 | 100.00 |
| C级来源交叉核验率 | 100.00 |
| 来源质量分 | 59.53 |
| 总分 | 73.26 |

## 文档入口

- [项目展示](docs/showcase.md)
- [适用场景](docs/use-cases.md)
- [Evidence Pack 交付包](docs/evidence-pack.md)
- [Benchmark Eval 评估](docs/benchmark-evals.md)
- [MCP 接入](docs/mcp-server.md)
- [路线图](docs/roadmap.md)
- [架构说明](docs/architecture.md)
- [贡献指南](CONTRIBUTING.md)

## 开发与贡献

本项目欢迎：

- 新案例
- 新的数据采集流程
- 更严格的验证 / QC 工具
- 更好的 Agent 集成方式

开始前请先看：

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [首次外部用户验证](docs/first-user-validation.md)

## 许可证

MIT
