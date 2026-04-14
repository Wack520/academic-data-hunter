# 任务规范：全国近十年人口数据（30省，2015-2024）

## 任务目标

补齐 `resident_population_10k_person`（年末常住人口，单位：万人）：
- 地理：30省（不含西藏、港澳台）
- 时间：2015-2024
- 单位：万人

## 输出文件

- 数据文件：`data/population_by_province.csv`
- 来源台账：`data/source_registry.csv`

## 字段要求

`population_by_province.csv`：
- `province`
- `year`
- `resident_population_10k_person`
- `source_id`
- `source_level`
- `source_name`
- `source_url`
- `publish_date`
- `access_date`
- `evidence`
- `note`

## 来源优先级

1. 国家统计局/省统计局官方
2. 省级统计公报/统计年鉴
3. C级来源仅作补充且必须有交叉核验

## 执行红线

- 禁止估算/推算/插值/外推
- 每条值必须有可访问 `source_url`
- 单位必须可追溯（若原始单位非万人需写清换算）
