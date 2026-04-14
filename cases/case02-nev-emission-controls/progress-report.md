# 进度报告（case02-nev-emission-controls）

更新时间：2026-03-26

## 已完成
- ✅ 新增自动采集脚本：`scripts/collect_case02.py`
- ✅ 新增导出脚本：`scripts/export_case02_xlsx.py`
- ✅ 新增对比脚本：`scripts/compare_case02_with_delivery.py`
- ✅ 新增一键QC脚本：`scripts/qc_case02.py`
- ✅ 实现 NBS 反爬 challenge 自动处理（多轮跳转 + JS求解）
- ✅ 自动抓取 7 个 NBS 指标（30省×2012-2023）
- ✅ 合并 NEV 保有量
- ✅ 构造 3 个派生控制变量（人均GDP/城镇化率/第三产业占比）
- ✅ 基于油耗估算交通碳排放
- ✅ 生成案例输出目录与台账
- ✅ 生成 xlsx 交付文件（panel/source_registry）
- ✅ 生成与交付目录对比报告
- ✅ 生成 auto-round 报告（当前缺口=0，提前停止）

## 本轮产出文件
- `cases/case02-nev-emission-controls/data/panel_case02_30prov_2012_2023.csv`
- `cases/case02-nev-emission-controls/data/panel_case02_30prov_2012_2023.xlsx`
- `cases/case02-nev-emission-controls/data/source_registry.csv`
- `cases/case02-nev-emission-controls/data/source_registry.xlsx`
- `cases/case02-nev-emission-controls/data/nbs_*.csv`
- `cases/case02-nev-emission-controls/comparison_with_delivery.md`
- `cases/case02-nev-emission-controls/next-round-task.md`
- `cases/case02-nev-emission-controls/auto-round-report.md`

## 覆盖率
- `transport_co2_est_10k_ton`: 360 / 360
- `nev_stock_10k`: 360 / 360
- `gdp_per_capita_yuan`: 360 / 360
- `urbanization_rate`: 360 / 360
- `passenger_turnover_100m_pkm`: 360 / 360
- `freight_turnover_100m_tkm`: 360 / 360
- `road_mileage_10k_km`: 360 / 360
- `tertiary_share`: 360 / 360

## 数据指纹
- `panel_case02_30prov_2012_2023.csv`
  - SHA256: `960ED20F00DF03B28EC998EB6DDDB504818E2C50ED86CD2EBC408B4CACD3A914`

## 备注
- “交通碳排放量”当前为估算口径（基于交通燃油消费），非官方直接发布的“交通部门碳排放”统计口径。
- 如后续拿到官方省级交通CO2直接口径，可在此面板替换 `transport_co2_est_10k_ton`。
- 与 `math/交付数据_30省面板_2012_2023` 的共同业务列仅 `nev_stock_10k`，当前重叠非空部分差异为 0。

---

## 严格口径追加（2026-03-26）

### 已完成
- ✅ 使用 CEADs 账号登录后下载 2012-2022 全部 `30个省份排放清单` 原始Excel（11份）
- ✅ 抽取交通部门 `Transportation, Storage, Post and Telecommunication Services` 的 `Scope_1_Total`
- ✅ 生成严格口径交通排放文件：
  - `data/raw_ceads_sectoral_30prov/ceads_transport_co2_direct_30prov_2012_2022.csv`
- ✅ 生成严格口径面板：
  - `data/panel_case02_strict_30prov_2012_2023.csv`
- ✅ 生成严格口径来源台账：
  - `data/source_registry_strict.csv`
- ✅ 新增严格 NEV 部分补采脚本：
  - `scripts/collect_case02_nev_strict_partial.py`
- ✅ 生成严格 NEV 已确认数据文件：
  - `data/nev_stock_strict_2023_partial.csv`

### 严格口径覆盖率（panel_case02_strict_30prov_2012_2023.csv）
- `transport_co2_10k_ton_direct`: 330 / 360（2012-2022各30省全覆盖，2023暂无官方发布）
- `nev_stock_10k`: 16 / 360（2023年已补齐16省：北京/天津/四川/安徽/山东/甘肃/贵州/浙江/上海/广东/广西/河北/河南/海南/湖南/重庆；其余留空）
- 其余控制变量（NBS）均为 360 / 360

### NEV 严格源扫描结论
- 已新增：
  - `strict-nev-source-scan.md`（官方源可得性核查）
  - `next-round-task-nev-strict.md`（逐省逐年补采任务单）
- 本轮已确认并入库（2023）：北京 77.3 万辆、天津 48 万辆、四川 89.63 万辆（电动汽车口径）、安徽 60.3 万辆（截至11月底口径）、山东 165.9 万辆（截至9月底口径）、甘肃 9.7879 万辆、贵州 27.48 万辆（截至2023-12-22口径）、浙江 204 万辆、上海 128.8 万辆、广东 289 万辆、广西 92.37 万辆（截至11月底口径）、河北 80.8 万辆、河南 114 万辆（电动汽车口径）、海南 27.3 万辆（截至10月底口径）、湖南 56.50 万辆、重庆 45 万辆。
- 结论：当前仍未发现单一官方API可直接拉取 30省×2012-2023 NEV 保有量，需要继续按“省级官方公报/年鉴”逐条采集路径补齐。
