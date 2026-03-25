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

## 项目结构

```
├── docs/           # 方法论文档
├── templates/      # 可复用模板（任务文档、进度汇报、来源台账）
├── tools/          # 通用工具（QC检查、面板合并、省份映射）
├── cases/          # 案例库
│   └── case01-nev-carbon/  # 案例1：新能源车碳减排（30省面板）
└── .agent/         # AI Agent 工作流配置
```

## 案例列表

| # | 案例 | 变量 | 面板规模 | 状态 |
|---|------|------|----------|------|
| 01 | [新能源车碳减排](cases/case01-nev-carbon/) | 充电桩、公交车、发电量、燃油消耗等17个 | 30省×2012-2023 | ✅ 完成 |

## 核心方法论

详见 [docs/methodology.md](docs/methodology.md)

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

## License

MIT
