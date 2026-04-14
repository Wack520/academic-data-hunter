# 搜索日志（case03-population-10y）

更新时间：2026-03-27

## Round 1（NBS 批量采集）

- 来源：国家统计局 国家数据（指标 A030101，2015-2024）
- 结果：已写入 `population_by_province.csv` 与 `source_registry.csv`
- 规则：严格模式，不插值、不估算
- 运行说明：当前环境在线 NBS 接口不可达，采用本地缓存 `case02/data/nbs_resident_population_10k_person.csv` 回填。
- 覆盖结果：2015-2023 为 30/30；2024 为 0/30（待补）。

## Round 2（2024 省级来源发现 + 短名单回填）

- 发现脚本：`scripts/discover_case03_population_2024.py`
- 发现输出：`cases/case03-population-10y/tmp/population_2024_candidates.json`
- 短名单脚本：`scripts/build_case03_population_2024_shortlist.py`
- 短名单输出：`cases/case03-population-10y/data/population_2024_shortlist_review.csv`
- 严格部分面板：`cases/case03-population-10y/data/population_by_province_strict_partial.csv`
- 严格部分台账：`cases/case03-population-10y/data/source_registry_strict_partial.csv`
- 结果：2024 年新增 12 省，覆盖从 0/30 提升至 12/30（仍缺 18 省）
- 说明：短名单为“自动提取待二审”口径，未覆盖主面板，避免误入库。

## Round 3（18省定向补采）

- 补采脚本：`scripts/collect_case03_population_2024_strict_remaining.py`
- 证据文件：`cases/case03-population-10y/data/population_2024_round3_evidence.csv`
- 结果：2024 年剩余 18 省全部补齐，严格部分面板达到 `300/300`。
- 备注：
  - 甘肃省来源页 requests 直连返回 412，采用 Camoufox 渲染后抽取正文；
  - 宁夏来源采用宁夏日报电子版转载统计公报全文（`szb.nxrb.cn`）。

## Round 4（同步回主面板）

- 同步脚本：`scripts/sync_case03_strict_to_main.py`
- 同步结果：
  - `population_by_province.csv` -> `300/300`
  - `source_registry.csv` -> 31 条来源记录
- 校验：`validate_round.py` 对主面板与主台账检查通过。
