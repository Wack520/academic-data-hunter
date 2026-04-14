# 任务规格（case02-nev-emission-controls）

## 研究目标
构建 30 省（不含西藏、港澳台）2012–2023 年面板，覆盖以下变量：

1. 交通碳排放量（估算）`transport_co2_est_10k_ton`
2. 新能源汽车保有量 `nev_stock_10k`
3. 人均GDP `gdp_per_capita_yuan`
4. 城镇化率 `urbanization_rate`
5. 客运周转量 `passenger_turnover_100m_pkm`
6. 货运周转量 `freight_turnover_100m_tkm`
7. 公路里程 `road_mileage_10k_km`
8. 第三产业占比 `tertiary_share`

## 数据口径与构造
- NBS 直接抓取（`data.stats.gov.cn`，数据库 `fsnd`）：
  - `A020101` 地区生产总值
  - `A020104` 第三产业增加值
  - `A030101` 年末常住人口
  - `A030102` 城镇人口
  - `A0G0401` 旅客周转量
  - `A0G0601` 货物周转量
  - `A0G0203` 公路里程
- 派生：
  - `gdp_per_capita_yuan = gdp_100m_cny * 10000 / resident_population_10k_person`
  - `urbanization_rate = urban_population_10k_person / resident_population_10k_person`
  - `tertiary_share = tertiary_value_added_100m_cny / gdp_100m_cny`
- NEV：
  - 使用本地历史采集产物 `math/data_collector/output/nev_stock_30prov_2012_2023.csv`
- 交通碳排放（估算）：
  - 油耗来源优先 `math/merged_output/all_priorities_merged_panel_30prov_2012_2023.csv`（含 `*_filled`）
  - 公式：`汽油*2.925 + 柴油*3.096`（tCO2 / t燃料）
  - 结果单位：`万吨CO2`

## 质量要求
- 主键唯一：`province,year`
- 年份完整：2012–2023 共 12 年
- 地区完整：30 省
- 关键变量覆盖率目标：>= 95%（当前结果为 100%）

## 执行脚本
```bash
python scripts/collect_case02.py
```

## 输出
- `data/panel_case02_30prov_2012_2023.csv`
- `data/source_registry.csv`
- `data/nbs_*.csv`（各指标抓取原始文件）

