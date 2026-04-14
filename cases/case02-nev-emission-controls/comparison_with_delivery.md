# Case02 与交付面板差异报告

- Case02: `D:\Desk\app\academic-data-hunter\cases\case02-nev-emission-controls\data\panel_case02_30prov_2012_2023.csv`
- Delivery: `D:\Desk\app\math\交付数据_30省面板_2012_2023\panel_30prov_2012_2023.csv`

## 基本信息
- Case02 shape: (360, 14)
- Delivery shape: (360, 17)
- Inner join on (province,year): 360 行

## 列集合差异
- 共同列（含键）数量: 3
- 仅 Case02 有: ['transport_co2_est_10k_ton', 'gdp_per_capita_yuan', 'urbanization_rate', 'passenger_turnover_100m_pkm', 'freight_turnover_100m_tkm', 'road_mileage_10k_km', 'tertiary_share', 'gdp_100m_cny', 'tertiary_value_added_100m_cny', 'resident_population_10k_person', 'urban_population_10k_person']
- 仅 Delivery 有: ['transport_value_added_100m_cny', 'total_generation_100m_kwh', 'hydro_generation_100m_kwh', 'thermal_generation_100m_kwh', 'clean_generation_100m_kwh', 'hydro_share', 'clean_power_ratio', 'gasoline_consumption_10k_ton', 'diesel_consumption_10k_ton', 'fuel_total_10k_ton', 'diesel_share_in_fuel', 'fuel_intensity_per_100m_cny', 'public_charging_piles', 'national_bev_buses']

## 共同业务列数值差异

| column | both_non_na | unequal_count | max_abs_diff | mean_abs_diff |
|---|---:|---:|---:|---:|
| nev_stock_10k | 60 | 0 | 0.000000 | 0.000000 |
