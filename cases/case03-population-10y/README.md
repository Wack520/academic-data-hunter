# 案例03：全国近十年人口数据（30省，2015-2024）

## 目标

构建 `30省 × 10年` 的人口面板（年末常住人口，单位：万人），用于回归与描述统计。

## 当前状态

- 面板骨架已创建：`300` 行（30省 × 2015-2024）
- 主面板已填充：`300/300`（已覆盖 2015-2024）
- 严格部分面板已填充：`300/300`（2024 已补齐 30 省）
- 当前待补（主面板/严格部分面板）：`0/300`
- 说明：当前环境在线 NBS 接口不可达，本轮采用本地 NBS 缓存回填 2015-2023。

## 文件结构

```
case03-population-10y/
├── data/
│   ├── population_by_province.csv
│   ├── source_registry.csv
│   ├── population_2024_shortlist_review.csv
│   ├── population_by_province_strict_partial.csv
│   ├── source_registry_strict_partial.csv
│   └── population_2024_round3_evidence.csv
├── task-spec.md
├── progress-report.md
├── search-log.md
├── next-round-task.md
└── tmp/
    ├── population_2024_candidates.json
    └── population_2024_shortlist_report.md
```

## 推荐执行顺序

1. 优先官方 API / 统计表（国家统计局、各省统计公报）
2. 用 `next-round-task.md` 逐轮补缺
3. 每轮后运行 QC 与台账校验

## 常用命令

```bash
python cases/case03-population-10y/scripts/collect_case03_population_nbs.py --year-start 2015 --year-end 2024

python cases/case03-population-10y/scripts/discover_case03_population_2024.py \
  --year 2024 \
  --run-mode headless \
  --engines google,tavily,bing,sogou,360 \
  --domain-filter gov.cn \
  --max-pages 12 \
  --max-fetch-pages 8 \
  --max-candidates 8 \
  --resume \
  --output cases/case03-population-10y/tmp/population_2024_candidates.json

python cases/case03-population-10y/scripts/build_case03_population_2024_shortlist.py

python cases/case03-population-10y/scripts/build_case03_population_strict_partial_panel.py

python cases/case03-population-10y/scripts/collect_case03_population_2024_strict_remaining.py

python cases/case03-population-10y/scripts/sync_case03_strict_to_main.py

python scripts/run_round.py \
  --data cases/case03-population-10y/data/population_by_province_strict_partial.csv \
  --value-col resident_population_10k_person \
  --keyword-name 年末常住人口 \
  --keyword-template1 "{省名} 2024 国民经济和社会发展统计公报 常住人口 万人 site:gov.cn" \
  --keyword-template2 "{省名} 2024 统计局 常住人口 万人 site:gov.cn" \
  --year-start 2024 \
  --year-end 2024 \
  --top-years 1 \
  --output cases/case03-population-10y/next-round-task.md

python scripts/validate_round.py \
  --data cases/case03-population-10y/data/population_by_province_strict_partial.csv \
  --registry cases/case03-population-10y/data/source_registry_strict_partial.csv \
  --variable resident_population_10k_person \
  --value-col resident_population_10k_person \
  --check-unit 万人
```
