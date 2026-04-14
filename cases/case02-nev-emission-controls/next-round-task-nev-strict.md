# 下一轮任务单（NEV 严格口径）

更新时间：2026-03-26

## 任务目标
补齐 `nev_stock_10k`（新能源汽车保有量）官方来源数据，口径要求：
- 地理：30省
- 时间：2012-2023（允许缺失，禁止插值）
- 来源：政府官方网站（统计局/公安/交管）
- 记录：`source_url`、原文摘录位置、单位、换算过程

## 当前进度（已完成十轮）
- 已入库（2023）：北京、天津、四川、安徽、山东、甘肃、贵州、浙江、上海、广东、广西、河北、河南、海南、湖南、重庆、云南、宁夏、山西、内蒙古、新疆、陕西、江苏（23省）
- 仍待补：吉林、江西、湖北、福建、辽宁、青海、黑龙江（7省）及更早年份

## 执行顺序（建议）
1. **先做 2023 年 30省全覆盖**（最新年，来源更集中）
2. 再做 2022、2021（近三年）
3. 最后回补 2012-2020

## 搜索模板（必须使用官方域名过滤）

### 模板A（统计公报）
`{省名} 2023 国民经济和社会发展统计公报 新能源汽车 保有量 site:gov.cn`

### 模板B（公安交管）
`{省名} 2023 机动车 保有量 新能源汽车 site:gov.cn`

### 模板C（统计年鉴）
`{省名} 统计年鉴 新能源汽车 保有量 site:gov.cn`

### 模板D（Camoufox 批量候选发现）
`python scripts/discover_case02_nev_camoufox.py --config templates/advanced-search-config.example.toml --resume --run-mode headless --output cases/case02-nev-emission-controls/tmp/camoufox_missing7_v2.json --engines google,tavily,bing,sogou,360 --max-pages 30 --fetch-workers 8 --domain-filter gov.cn`

### 模板E（全自动续跑，不需逐轮人工继续）
`python scripts/run_case02_nev_strict_autopilot.py --rounds 3 --run-mode headless --engines google,tavily,bing,sogou,360 --max-pages 30 --max-fetch-pages 20 --fetch-workers 8 --domain-filter gov.cn --skip-collect`

> 该命令默认会在 discover 后自动执行处理层（markdown归档 + schema抽取）；如只搜索可加 `--skip-processing`。

## 入库要求（严格）
- 原文出现“新能源汽车保有量/拥有量/登记量”且能对应年末或年度存量口径；
- 单位统一转换到“万辆”（`nev_stock_10k`）；
- 若仅有“新增量/销量/产量”，**不得替代**保有量；
- 找不到就留空，不得估算。

## 交付文件
- 目标数据文件：`cases/case02-nev-emission-controls/data/panel_case02_strict_30prov_2012_2023.csv`
- 来源台账：`cases/case02-nev-emission-controls/data/source_registry_strict.csv`
- 搜索日志：`cases/case02-nev-emission-controls/search-log.md`（追加 NEV 严格条目）
