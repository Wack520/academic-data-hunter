# case02-nev-emission-controls

本案例输出 30省 × 2012-2023 的控制变量面板，目标变量如下：
- `transport_co2_est_10k_ton`（交通碳排放估算）
- `nev_stock_10k`（新能源汽车保有量）
- `gdp_per_capita_yuan`（人均GDP）
- `urbanization_rate`（城镇化率）
- `passenger_turnover_100m_pkm`（客运周转量）
- `freight_turnover_100m_tkm`（货运周转量）
- `road_mileage_10k_km`（公路里程）
- `tertiary_share`（第三产业占比）

## 文件说明
- `task-spec.md`：任务规格
- `progress-report.md`：执行进展与覆盖率
- `search-log.md`：搜索/采集日志
- `comparison_with_delivery.md`：与 `math/交付数据_30省面板_2012_2023` 对比报告
- `next-round-task.md`：自动补缺任务单（本轮已无缺口）
- `auto-round-report.md`：自动多轮调度报告
- `data/panel_case02_30prov_2012_2023.csv`：最终面板
- `data/source_registry.csv`：来源台账
- `data/nbs_*.csv`：分指标原始抓取文件

## 复现命令
```bash
python cases/case02-nev-emission-controls/scripts/collect_case02.py
python cases/case02-nev-emission-controls/scripts/export_case02_xlsx.py
python cases/case02-nev-emission-controls/scripts/qc_case02.py
python cases/case02-nev-emission-controls/scripts/compare_case02_with_delivery.py
python scripts/run_round.py --data cases/case02-nev-emission-controls/data/panel_case02_30prov_2012_2023.csv --value-col transport_co2_est_10k_ton --keyword-name 交通碳排放估算 --keyword-template1 "{省名} {keyword_name} {year}" --keyword-template2 "{省名} 交通运输 二氧化碳排放 {year}" --year-start 2012 --year-end 2023 --top-years 2 --output cases/case02-nev-emission-controls/next-round-task.md
python scripts/run_auto_rounds.py --data cases/case02-nev-emission-controls/data/panel_case02_30prov_2012_2023.csv --value-col transport_co2_est_10k_ton --year-start 2012 --year-end 2023 --max-rounds 2 --task-output cases/case02-nev-emission-controls/next-round-task.md --report cases/case02-nev-emission-controls/auto-round-report.md
```

## 说明
- NBS 指标由脚本自动采集（含 challenge 处理）。
- 交通碳排放为基于油耗的估算值（非官方直接发布“交通碳排放”统计口径）。
- 生成时间：2026-03-25 20:07:27

## 严格口径（真实直采）补充

新增严格流程文件：
- `data/raw_ceads_sectoral_30prov/*.xlsx`：CEADs 2012-2022「30个省份排放清单」原始下载
- `data/raw_ceads_sectoral_30prov/ceads_transport_co2_direct_30prov_2012_2022.csv`：交通部门直接排放提取结果
- `data/panel_case02_strict_30prov_2012_2023.csv`：严格口径面板（交通排放使用 CEADs 直接值）
- `data/source_registry_strict.csv`：严格口径来源台账

严格流程命令：
```bash
# 1) 下载 CEADs 30省排放清单（需 CEADS_USERNAME / CEADS_PASSWORD）
python cases/case02-nev-emission-controls/scripts/download_ceads_sectoral_30prov.py

# 2) 提取交通部门直接排放（Scope_1_Total）
python cases/case02-nev-emission-controls/scripts/extract_ceads_transport_direct.py

# 3) 生成严格面板
python cases/case02-nev-emission-controls/scripts/build_case02_strict_panel.py

# 4) 补采严格 NEV（当前为2023年已确认省份）
python cases/case02-nev-emission-controls/scripts/collect_case02_nev_strict_partial.py
```

严格口径当前覆盖（2026-03-26）：
- `transport_co2_10k_ton_direct`：330/360（2012-2022全覆盖，2023暂缺）
- `nev_stock_10k`：16/360（2023年：北京/天津/四川/安徽/山东/甘肃/贵州/浙江/上海/广东/广西/河北/河南/海南/湖南/重庆已补齐；其余留空待补）
