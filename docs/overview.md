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
