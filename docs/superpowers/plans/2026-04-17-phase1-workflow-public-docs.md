# Workflow-First Public Docs Repositioning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reposition the repo's public surfaces around a workflow-first narrative by adding canonical docs, rewriting README, and turning case-centric docs into compatibility pages without moving directories yet.

**Architecture:** Phase 1 only changes public documentation, navigation, and repo narrative. New canonical docs under `docs/` become the source of truth for overview, workflow, user guides, source policy, validation, integrations, and examples; existing case-centric docs remain as short bridge pages so inbound links do not break before the later `cases/ -> examples/` migration.

**Tech Stack:** Markdown, PowerShell, Python 3, git, `scripts/check_docs_command_paths.py`, pytest

---

## File Structure

### Canonical docs to create

- `docs/overview.md` — project identity, audience, outputs, and scope
- `docs/workflow.md` — end-to-end workflow from task spec to benchmark eval
- `docs/researcher-guide.md` — how a research / analysis user runs the workflow
- `docs/developer-guide.md` — how a developer / agent user integrates the workflow
- `docs/source-policy.md` — source grading and admission rules
- `docs/validation.md` — quality checks and acceptance criteria
- `docs/benchmark-eval.md` — canonical benchmark/eval explanation page
- `docs/integrations-mcp.md` — canonical MCP integration page
- `docs/examples.md` — explains current examples and future `examples/` direction

### Existing files to modify

- `README.md` — new workflow-first landing page and canonical doc links
- `docs/evidence-pack.md` — align wording with workflow-first narrative
- `docs/roadmap.md` — reflect phased repositioning work
- `docs/showcase.md` — compatibility page to `docs/examples.md`
- `docs/use-cases.md` — compatibility page to `docs/researcher-guide.md` and `docs/examples.md`
- `docs/positioning.md` — compatibility page to `docs/overview.md`
- `docs/mcp-server.md` — compatibility page to `docs/integrations-mcp.md`
- `docs/benchmark-evals.md` — compatibility page to `docs/benchmark-eval.md`

### Validation commands used throughout

- `python scripts/check_docs_command_paths.py --paths README.md CONTRIBUTING.md docs .github`
- `python -m pytest -q`

---

### Task 1: Add the canonical overview and workflow docs

**Files:**
- Create: `docs/overview.md`
- Create: `docs/workflow.md`
- Test: inline Python existence assertion

- [ ] **Step 1: Write the failing existence test**

```python
from pathlib import Path
required = [
    "docs/overview.md",
    "docs/workflow.md",
]
missing = [p for p in required if not Path(p).exists()]
assert not missing, f"missing docs: {missing}"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
@'
from pathlib import Path
required = [
    "docs/overview.md",
    "docs/workflow.md",
]
missing = [p for p in required if not Path(p).exists()]
assert not missing, f"missing docs: {missing}"
'@ | python -
```

Expected: FAIL with `missing docs` because both files do not exist yet.

- [ ] **Step 3: Write the minimal implementation**

```powershell
@'
# 项目总览

Academic Data Hunter 是一套**公开数据采集与交付工作流框架**。

它把“找数据”组织成一条可复用 workflow：

- 定义任务
- 检索公开来源
- 抽取结构化字段
- 登记来源与证据
- 执行质量校验
- 导出交付包
- 输出量化评估

## 适合谁用

### 研究 / 分析用户

当你需要的不只是一个搜索结果，而是一份**可继续分析、可回溯来源、可交接复核**的数据资产时，可以直接使用这套 workflow。

### 开发者 / Agent 用户

当你需要把公开数据搜集能力接到 CLI、API、MCP 或 Agent 工作流里时，可以把这套 workflow 当作数据层、证据层与评估层使用。

## 最终交付物

一次完整运行的典型输出包括：

- `dataset.csv`
- `source_registry.csv`
- `evidence_records.jsonl`
- `evidence pack`
- `benchmark eval`

## 边界

项目不以某一个案例、国家或数据题材定义自己，而以 workflow 能力定义自己。当前仓库里的 `cases/` 目录仅代表现有示例，不代表项目边界。
'@ | Set-Content docs/overview.md -Encoding UTF8

@'
# Workflow

Academic Data Hunter 的核心不是单次搜索，而是一整条公开数据采集与交付流程。

## 1. 任务定义

先用任务文档明确：

- 指标名称
- 单位
- 时间范围
- 空间范围
- 来源要求
- 红线约束

## 2. 来源检索

围绕任务文档，从公开来源中检索候选页面、数据库、报告、附录和表格。

## 3. 结构化抽取

把候选来源中的值、单位、年份、实体、证据语句和来源链接抽取出来，整理成结构化记录。

## 4. 来源登记

把来源写入 `source_registry.csv`，记录来源等级、访问日期、交叉核验信息和证据文件引用。

## 5. 数据校验

检查：

- 必填字段
- 单位一致性
- 主键重复
- 台账匹配
- 来源等级规则

## 6. 交付包导出

将数据表、来源台账、证据记录和说明文件打包成 Evidence Pack。

## 7. 量化评估

用 Benchmark Eval 评估当前结果的完整性、来源质量和交付可用性。

## 当前阶段说明

当前仓库仍保留 `cases/` 目录作为示例资产；后续阶段再迁移为 `examples/`。
'@ | Set-Content docs/workflow.md -Encoding UTF8
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
@'
from pathlib import Path
required = [
    "docs/overview.md",
    "docs/workflow.md",
]
missing = [p for p in required if not Path(p).exists()]
assert not missing, f"missing docs: {missing}"
print("overview/workflow docs created")
'@ | python -
```

Expected: PASS and print `overview/workflow docs created`.

- [ ] **Step 5: Commit**

```bash
git add docs/overview.md docs/workflow.md
git commit -m "docs: add overview and workflow guides"
```

### Task 2: Add user guides and workflow policy docs

**Files:**
- Create: `docs/researcher-guide.md`
- Create: `docs/developer-guide.md`
- Create: `docs/source-policy.md`
- Create: `docs/validation.md`
- Test: inline Python existence assertion

- [ ] **Step 1: Write the failing existence test**

```python
from pathlib import Path
required = [
    "docs/researcher-guide.md",
    "docs/developer-guide.md",
    "docs/source-policy.md",
    "docs/validation.md",
]
missing = [p for p in required if not Path(p).exists()]
assert not missing, f"missing docs: {missing}"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
@'
from pathlib import Path
required = [
    "docs/researcher-guide.md",
    "docs/developer-guide.md",
    "docs/source-policy.md",
    "docs/validation.md",
]
missing = [p for p in required if not Path(p).exists()]
assert not missing, f"missing docs: {missing}"
'@ | python -
```

Expected: FAIL with `missing docs` because the new guide/policy files do not exist yet.

- [ ] **Step 3: Write the minimal implementation**

```powershell
@'
# 研究用户指南

这份指南给研究、论文、建模和分析用户使用。

## 典型流程

1. 准备任务文档
2. 搜集公开来源
3. 写入来源台账
4. 跑校验
5. 导出 Evidence Pack
6. 查看 Benchmark Eval

## 任务文档至少要写清楚

- 指标名称
- 单位
- 年份范围
- 实体范围
- 来源要求
- 禁止事项（例如禁止估算）

## 交付验收时要看什么

- 数据值是否有来源
- 来源是否能回溯
- 台账是否匹配
- 证据记录是否齐全
- 当前结果是否足够进入后续分析
'@ | Set-Content docs/researcher-guide.md -Encoding UTF8

@'
# 开发者指南

这份指南给需要集成 workflow 的开发者使用。

## 你可以怎样接入

- 直接调用 CLI 脚本
- 通过 API 进程调用
- 通过本地 MCP server 暴露工具

## 推荐接入思路

1. 先把任务定义标准化
2. 把数据采集和抽取结果落盘
3. 始终产出来源台账
4. 在交付前跑校验和 Benchmark Eval

## 当前可直接复用的能力

- run round
- validate round
- evidence pack export
- benchmark eval
'@ | Set-Content docs/developer-guide.md -Encoding UTF8

@'
# 来源策略

项目允许使用不同类型的公开来源，但采用“高质量来源优先”的规则。

## 优先顺序

1. 政府 / 国际组织 / 官方数据库
2. 高校 / 论文附录 / 学术补充材料
3. 行业协会 / 智库 / 研究机构
4. 媒体 / 第三方网页

## 入库原则

- 所有来源都可以搜索
- 不是所有来源都能同等强度入库
- 来源越弱，越需要 cross-check
- 如果高等级来源与低等级来源冲突，以高等级来源为准

## 最低要求

入库记录至少要有：

- `source_url`
- 来源等级
- `access_date`
- 必要时的 `cross_check_url`
'@ | Set-Content docs/source-policy.md -Encoding UTF8

@'
# 校验说明

交付前至少要做以下检查。

## 行级检查

- 必填字段存在
- 主键不重复
- 数值字段可解析
- 单位与口径一致
- 来源字段完整

## 表级检查

- 数据表与来源台账能匹配
- evidence 记录与数据表能对应
- 覆盖率变化可解释

## 当前仓库中的常用检查

- `python scripts/validate_round.py`
- `python scripts/check_docs_command_paths.py --paths README.md CONTRIBUTING.md docs .github`
- `python -m pytest -q`
'@ | Set-Content docs/validation.md -Encoding UTF8
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
@'
from pathlib import Path
required = [
    "docs/researcher-guide.md",
    "docs/developer-guide.md",
    "docs/source-policy.md",
    "docs/validation.md",
]
missing = [p for p in required if not Path(p).exists()]
assert not missing, f"missing docs: {missing}"
print("user guides and policy docs created")
'@ | python -
```

Expected: PASS and print `user guides and policy docs created`.

- [ ] **Step 5: Commit**

```bash
git add docs/researcher-guide.md docs/developer-guide.md docs/source-policy.md docs/validation.md
git commit -m "docs: add workflow guides and policy docs"
```

### Task 3: Create canonical integration/example pages and rewrite README

**Files:**
- Create: `docs/benchmark-eval.md`
- Create: `docs/integrations-mcp.md`
- Create: `docs/examples.md`
- Modify: `README.md`
- Test: inline Python content assertion on README and new files

- [ ] **Step 1: Write the failing README/content test**

```python
from pathlib import Path
text = Path("README.md").read_text(encoding="utf-8")
assert "公开数据采集与交付工作流框架" in text
assert "docs/overview.md" in text
assert "docs/workflow.md" in text
for path in [
    "docs/benchmark-eval.md",
    "docs/integrations-mcp.md",
    "docs/examples.md",
]:
    assert Path(path).exists(), path
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
@'
from pathlib import Path
text = Path("README.md").read_text(encoding="utf-8")
assert "公开数据采集与交付工作流框架" in text
assert "docs/overview.md" in text
assert "docs/workflow.md" in text
for path in [
    "docs/benchmark-eval.md",
    "docs/integrations-mcp.md",
    "docs/examples.md",
]:
    assert Path(path).exists(), path
'@ | python -
```

Expected: FAIL because the new canonical docs do not exist and README still points to the older doc layout.

- [ ] **Step 3: Write the minimal implementation**

```powershell
@'
# Benchmark Eval

Benchmark Eval 用来回答一个直接问题：当前这次数据交付，是否足够进入下一步研究或系统使用。

## 当前关注的维度

- 覆盖率
- 来源完整性
- 台账匹配率
- 交叉核验情况
- 来源质量分

## 它解决的问题

只看“找到了多少数据”并不够。Benchmark Eval 用来补上“这批结果是否可信、是否完整、是否可交付”的量化视角。
'@ | Set-Content docs/benchmark-eval.md -Encoding UTF8

@'
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
'@ | Set-Content docs/integrations-mcp.md -Encoding UTF8

@'
# 示例

当前仓库中的 `cases/` 目录代表**现有示例资产**，不是项目边界。

## 当前已有示例

- 中国区域面板类任务
- 控制变量补齐任务
- 人口数据整理任务

## 后续方向

后续会逐步迁移到 `examples/` 目录，并补充：

- `global-public-stats`
- `paper-appendix-extraction`

## 为什么要这样做

示例的职责是证明 workflow 可以落到不同公开数据任务上，而不是反过来定义 workflow 本身。
'@ | Set-Content docs/examples.md -Encoding UTF8

@'
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

## 许可证

MIT
'@ | Set-Content README.md -Encoding UTF8
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
@'
from pathlib import Path
text = Path("README.md").read_text(encoding="utf-8")
assert "公开数据采集与交付工作流框架" in text
assert "docs/overview.md" in text
assert "docs/workflow.md" in text
for path in [
    "docs/benchmark-eval.md",
    "docs/integrations-mcp.md",
    "docs/examples.md",
]:
    assert Path(path).exists(), path
print("README and canonical docs rewired")
'@ | python -
```

Expected: PASS and print `README and canonical docs rewired`.

- [ ] **Step 5: Commit**

```bash
git add README.md docs/benchmark-eval.md docs/integrations-mcp.md docs/examples.md
git commit -m "docs: reframe README around workflow-first narrative"
```

### Task 4: Align legacy docs, preserve compatibility links, and verify the repo

**Files:**
- Modify: `docs/evidence-pack.md`
- Modify: `docs/roadmap.md`
- Modify: `docs/showcase.md`
- Modify: `docs/use-cases.md`
- Modify: `docs/positioning.md`
- Modify: `docs/mcp-server.md`
- Modify: `docs/benchmark-evals.md`
- Test: README/docs content assertion, command-path check, full pytest run

- [ ] **Step 1: Write the failing compatibility/content test**

```python
from pathlib import Path
checks = {
    "docs/showcase.md": "docs/examples.md",
    "docs/use-cases.md": "docs/researcher-guide.md",
    "docs/positioning.md": "docs/overview.md",
    "docs/mcp-server.md": "docs/integrations-mcp.md",
    "docs/benchmark-evals.md": "docs/benchmark-eval.md",
}
for file, target in checks.items():
    text = Path(file).read_text(encoding="utf-8")
    assert target in text, f"{file} does not point to {target}"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
@'
from pathlib import Path
checks = {
    "docs/showcase.md": "docs/examples.md",
    "docs/use-cases.md": "docs/researcher-guide.md",
    "docs/positioning.md": "docs/overview.md",
    "docs/mcp-server.md": "docs/integrations-mcp.md",
    "docs/benchmark-evals.md": "docs/benchmark-eval.md",
}
for file, target in checks.items():
    text = Path(file).read_text(encoding="utf-8")
    assert target in text, f"{file} does not point to {target}"
'@ | python -
```

Expected: FAIL because the legacy docs still contain older standalone content.

- [ ] **Step 3: Write the minimal implementation**

```powershell
@'
# Evidence Pack

Evidence Pack 是 workflow 的核心交付物之一。

它把数据表、来源台账、证据记录和说明文件一起交付出去，让结果可以复核、交接和继续分析。

## 当前结构

- `dataset.csv`
- `source_registry.csv`
- `evidence_records.jsonl`
- `README.md`
- `manifest.json`

## 相关文档

- [项目总览](overview.md)
- [Workflow](workflow.md)
- [校验说明](validation.md)
- [Benchmark Eval](benchmark-eval.md)
'@ | Set-Content docs/evidence-pack.md -Encoding UTF8

@'
# 路线图

## Phase 1：公开叙事与文档重构

- README 改成 workflow-first
- docs 改成能力导向
- 把 `cases/` 在文档中降级为示例概念

## Phase 2：示例目录重组

- 规划 `examples/` 结构
- 将 `cases/` 迁移为 `examples/`
- 统一示例目录规范

## Phase 3：新增示例

- 补 `global-public-stats`
- 补 `paper-appendix-extraction`

## Phase 4：命名与品牌升级

- 评估 repo 命名是否需要调整
- 评估对外展示与发布节奏
'@ | Set-Content docs/roadmap.md -Encoding UTF8

@'
# 项目展示（兼容入口）

当前规范化的示例说明已迁移到：

- [示例](examples.md)
- [项目总览](overview.md)
'@ | Set-Content docs/showcase.md -Encoding UTF8

@'
# 适用场景（兼容入口）

当前适用场景与使用方式已迁移到：

- [研究用户指南](researcher-guide.md)
- [示例](examples.md)
'@ | Set-Content docs/use-cases.md -Encoding UTF8

@'
# 定位说明（兼容入口）

当前项目主定位已迁移到：

- [项目总览](overview.md)
- [Workflow](workflow.md)
'@ | Set-Content docs/positioning.md -Encoding UTF8

@'
# MCP 接入（兼容入口）

当前 MCP 说明已迁移到：

- [MCP 集成](integrations-mcp.md)
'@ | Set-Content docs/mcp-server.md -Encoding UTF8

@'
# Benchmark Eval（兼容入口）

当前 Benchmark Eval 说明已迁移到：

- [Benchmark Eval](benchmark-eval.md)
'@ | Set-Content docs/benchmark-evals.md -Encoding UTF8
```

- [ ] **Step 4: Run tests to verify it passes**

Run:

```powershell
@'
from pathlib import Path
checks = {
    "docs/showcase.md": "examples.md",
    "docs/use-cases.md": "researcher-guide.md",
    "docs/positioning.md": "overview.md",
    "docs/mcp-server.md": "integrations-mcp.md",
    "docs/benchmark-evals.md": "benchmark-eval.md",
}
for file, target in checks.items():
    text = Path(file).read_text(encoding="utf-8")
    assert target in text, f"{file} does not point to {target}"
print("legacy docs now point to canonical docs")
'@ | python -
python scripts/check_docs_command_paths.py --paths README.md CONTRIBUTING.md docs .github
python -m pytest -q
```

Expected:

- PASS and print `legacy docs now point to canonical docs`
- `docs command path check passed`
- `pytest` exits with `0 failures`

- [ ] **Step 5: Commit**

```bash
git add docs/evidence-pack.md docs/roadmap.md docs/showcase.md docs/use-cases.md docs/positioning.md docs/mcp-server.md docs/benchmark-evals.md
git commit -m "docs: align legacy pages with workflow docs"
```

---

## Self-Review

### Spec coverage

This plan intentionally covers only **Phase 1** of the approved spec:

- README workflow-first repositioning
- canonical docs creation
- doc navigation restructuring
- `cases/` conceptually downgraded to examples in docs

It does **not** yet implement:

- actual `cases/ -> examples/` directory migration
- example directory renaming
- `global-public-stats` example
- `paper-appendix-extraction` example
- repo renaming

Those should be written as separate follow-on plans after Phase 1 lands cleanly.

### Placeholder scan

Search the finished plan for `TBD`, `TODO`, `implement later`, `fill in details`, and remove any occurrence before execution.

### Type consistency

The canonical doc filenames used in all tasks are:

- `docs/overview.md`
- `docs/workflow.md`
- `docs/researcher-guide.md`
- `docs/developer-guide.md`
- `docs/source-policy.md`
- `docs/validation.md`
- `docs/benchmark-eval.md`
- `docs/integrations-mcp.md`
- `docs/examples.md`

No later task should refer to alternate names.
