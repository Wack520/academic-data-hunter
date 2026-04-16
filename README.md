# Academic Data Hunter

> 公开数据采集与交付工作流框架

[![CI](https://github.com/Wack520/academic-data-hunter/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Wack520/academic-data-hunter/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Evidence Pack](https://img.shields.io/badge/Delivery-Evidence%20Pack-success)](docs/evidence-pack.md)
[![Benchmark Eval](https://img.shields.io/badge/Reliability-Benchmark%20Eval-purple)](docs/benchmark-eval.md)
[![MCP Server](https://img.shields.io/badge/MCP-local%20stdio-blue)](docs/integrations-mcp.md)

从公开来源检索、抽取、校验并交付可复核数据资产。

既可用于研究、论文、建模与分析，也可作为 Agent / MCP 工作流的数据层接入。

## 这是什么

Academic Data Hunter 用来把“找数据”变成“交付数据”。

它覆盖的是一整条 workflow，而不是单次搜索结果：

- 任务定义
- 来源检索
- 结构化抽取
- 来源登记
- 数据校验
- Evidence Pack
- Benchmark Eval

## 最终交付物

```text
task spec
  -> dataset.csv
  -> source_registry.csv
  -> evidence_records.jsonl
  -> evidence pack
  -> benchmark eval
```

## 给谁用

### 研究 / 分析用户

- 定义公开数据任务
- 组织来源搜集与抽取
- 校验并交付可复核数据包

### 开发者 / Agent 用户

- 通过 CLI / API / MCP 接入 workflow
- 把 workflow 作为数据层与证据层
- 给 Agent 增加交付与评估能力

## 当前示例

当前仓库仍使用 `cases/` 目录保存示例资产；这些目录代表**现有 examples**，不代表项目边界。

| 当前目录 | 当前角色 |
|---|---|
| `cases/case01-nev-carbon/` | 中国区域面板类示例 |
| `cases/case02-nev-emission-controls/` | 控制变量补齐类示例 |
| `cases/case03-population-10y/` | 公共统计整理类示例 |

## 文档入口

- [项目总览](docs/overview.md)
- [Workflow](docs/workflow.md)
- [研究用户指南](docs/researcher-guide.md)
- [开发者指南](docs/developer-guide.md)
- [来源策略](docs/source-policy.md)
- [校验说明](docs/validation.md)
- [Evidence Pack](docs/evidence-pack.md)
- [Benchmark Eval](docs/benchmark-eval.md)
- [MCP 集成](docs/integrations-mcp.md)
- [示例](docs/examples.md)
- [路线图](docs/roadmap.md)
- [贡献指南](CONTRIBUTING.md)

## 快速开始

### 1）准备任务模板

```bash
cp templates/task-spec-template.md my-task.md
```

### 2）做数据校验

```powershell
python scripts/validate_round.py ^
  --data cases/case01-nev-carbon/data/charging_piles_by_province.csv ^
  --registry cases/case01-nev-carbon/data/source_registry.csv ^
  --variable charging ^
  --value-col public_charging_piles ^
  --check-unit 台
```

### 3）导出交付包

```powershell
python scripts/export_evidence_pack.py ^
  --data cases/case01-nev-carbon/data/charging_piles_by_province.csv ^
  --registry cases/case01-nev-carbon/data/source_registry.csv ^
  --variable charging ^
  --value-col public_charging_piles ^
  --output-dir tmp/evidence-pack/case01-charging
```

### 4）运行评估

```powershell
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

## 许可证

MIT
