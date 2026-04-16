# 案例01：新能源汽车碳减排研究（30省面板 2012-2023）

## 背景

学术研究竞赛课题：分析新能源汽车推广对中国交通碳减排的影响。

## 数据概况

| 指标 | 数值 |
|------|------|
| 面板规模 | 30省 × 12年 = 360行 |
| 变量数 | 17列 |
| 搜集耗时 | 约2天（含AI协作） |

## 核心变量

| 变量 | 覆盖率 | 来源 |
|------|--------|------|
| 交通增加值 | 100% | 国家统计局API |
| 发电量（总/水/火/清洁） | 100% | 国家统计局API |
| 燃油消耗（汽油+柴油） | 91.7% | CEADs数据库 |
| 新能源车保有量 | 16.7% | 公安部/各省公报 |
| **公共充电桩** | **23.9%** | 充电联盟/省政府/媒体 |
| **全国纯电动公交车** | **33.3%** | 交通运输部统计公报 |

## 搜集过程

详见本目录下的文件：
- [task-spec.md](task-spec.md) — 给AI Agent的任务规范（v2可审计版）
- [progress-report.md](progress-report.md) — 搜集过程的详细记录
- [search-log.md](search-log.md) — 搜索过程和关键发现

## 使用方法

```bash
# QC检查充电桩数据
python ../../tools/qc_checker.py data/charging_piles_by_province.csv

# 合并到面板
python ../../tools/panel_merger.py \
  --base data/panel_30prov_2012_2023.csv \
  --new data/charging_piles_by_province.csv \
  --on province,year \
  --map-province full
```

## 数据文件

```
data/
├── panel_30prov_2012_2023.csv       # 最终面板（360×17）
├── charging_piles_by_province.csv   # 充电桩分省数据（86条）
├── national_ev_bus_annual.csv       # 全国公交车年度数据
├── source_registry.csv              # 来源台账
└── 数据来源说明.md                   # 来源说明
```

## 关键经验

1. **充电桩分省数据**：2023年最充分（头豹研究院有完整30省图表），早期年份主要靠充电联盟年报和行业媒体
2. **新能源公交车**：分省数据不存在公开渠道，最终改用全国数据作为控制变量
3. **搜索效率**：in-en.com（国际能源网）是充电桩分省数据最丰富的站点
4. **AI协作**：任务组织型 Agent 负责初步搜索与规范整理，执行型 Agent 负责按规范系统深挖，效率最高
