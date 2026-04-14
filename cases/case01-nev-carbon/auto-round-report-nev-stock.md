# 自动多轮搜索报告（2026-03-25T17:39:35）

- 数据文件：`cases/case01-nev-carbon/data/panel_30prov_2012_2023.csv`
- 主键：`province,year`
- 数值列：`nev_stock_10k`
- 轮数上限：2

## 初始状态
- 已覆盖键数：60 / 360 (16.7%)
- 年份缺失总数（按 `nev_stock_10k`）：300

## Round 1
- 本轮前缺失总数：300
- 任务文件：`cases/case01-nev-carbon/next-round-task-nev-stock.md`
- 未提供 --agent-cmd，本轮为 Dry Run（仅生成任务）。

## 最终结果
- 实际执行轮数：1
- 最终覆盖键数：60 / 360 (16.7%)
- 各数值列非空：{'nev_stock_10k': 60}
- 各年份覆盖（按任一value-col有值）：{2022: 30, 2023: 30}

