# 数据搜集进度汇报（最新执行结果，2026-03-24）

## 本轮已执行（按优先级）

### 优先级1：公共充电桩补充
- 已更新文件：`d:\Desk\app\math\data_collector\output\charging_piles_by_province.csv`
- 同步导出：`charging_piles_by_province.xlsx`
- 结果：
  - 总记录由 **51条 → 66条**
  - **2023年覆盖由15省 → 30省（已补齐甘肃/青海/江西/新疆）**
  - 新补充记录来源为 C 级（头豹图表提取，已标注 `source_url`）
  - 既有 A/B 级记录优先保留（同省同年去重按 A>B>C）

### 优先级2：全国纯电动公交车年度数据补充
- 已重建文件：`d:\Desk\app\math\data_collector\output\national_ev_bus_annual.csv`
- 同步导出：`national_ev_bus_annual.xlsx`
- 采用策略：仅保留“可核验来源”数据，不做插值、不做AI生成
- 当前可用年份（`national_bev_buses`）：
  - 2019（由交通运输部公报总量+占比做确定性换算）
  - 2021（交通运输部公报原值）
  - 2022（交通运输部公报原值）
  - 2023（交通运输部公报原值，证据文件本地留存）
- 其余年份未检索到可自由访问且可核验原值，按规则留空。

### 优先级3：合并主面板
- 已更新文件：`d:\Desk\app\math\merged_output\panel_with_charging_buses_30prov.csv`
- 同步导出：`panel_with_charging_buses_30prov.xlsx`
- 合并规则：
  - 充电桩：按 `province + year` 左连接
  - 全国纯电动公交：按 `year` 广播到各省
- 合并后规模：`360 × 20`
  - `public_charging_piles` 非空：66
  - `nev_buses` 非空：120（4年 × 30省）

## 来源台账
- 已更新：`d:\Desk\app\math\data_collector\output\source_registry.csv`
- 同步导出：`source_registry.xlsx`
- 本轮新增/重构：
  - 充电桩来源ID（稳定哈希+固定ID）
  - 公交车来源ID（`SRC_NB_MOT_*`）

## 仍需继续的缺口（客观保留）
1. 充电桩：2016-2022 多省份仍缺失（公开省级年末值本就稀缺）
2. 公交车：2012-2018、2020 仍缺乏可核验全国纯电动原值（按规则留空）

## 执行红线（已遵守）
- 未做插值/外推/AI造数
- 每条入库值保留来源信息
- 搜不到即留空

---

## 本次追加执行：充电桩 2018-2022 缺失省份专项（2026-03-24 晚）

### 1) 执行动作
- 读取并核对：`charging_piles_by_province.csv`，按 2018-2022 年逐年识别缺失省份
- 按“省名+年份+公共充电桩/充电基础设施”检索，优先尝试 in-en 站内路径
- 新增可直接核验的省级数值后，回写：
  - `data_collector/output/charging_piles_by_province.csv`
  - `data_collector/output/charging_piles_by_province.xlsx`
- 同步更新来源台账：
  - `data_collector/output/source_registry.csv`
  - `data_collector/output/source_registry.xlsx`
- 重跑合并（充电桩来源ID同步）：
  - `merged_output/panel_with_charging_buses_30prov.csv`
  - `merged_output/panel_with_charging_buses_30prov.xlsx`

### 2) 本次新增数据（仅补缺，不覆盖已有省年）
- 充电桩记录：**+9条**（66 → 75）
- 新增来源ID：**+2条**（34 → 36）
  - `SRC_CP_INEN_2021AUG_TOP3`
  - `SRC_CP_INEN_2022_TOP10`

新增省年：
- 2021：北京、广东
- 2022：上海、北京、湖北、山东、安徽、河南、福建

### 3) 覆盖变化（2018-2022）
- 2018：缺失 28（不变）
- 2019：缺失 23（不变）
- 2020：缺失 23（不变）
- 2021：缺失 **27 → 25**
- 2022：缺失 **23 → 16**

### 4) 合并与QC结果
- 合并面板规模：`360 × 20`（不变）
- `public_charging_piles` 非空：**66 → 75**
- `province + year` 唯一性：通过（无重复）
- 充电桩记录 `source_id` 映射：通过（无空映射）

### 5) 说明
- 本轮新增值均来自可定位URL的文本数值；未做插值、外推或AI造数
- 2018-2020 仍缺口较大，后续继续按“可核验原文数值优先，搜不到留空”原则推进

---

## 本次继续执行（按你给的策略，2026-03-24 夜）

### 策略执行顺序
1. 先补 2022（缺口最少）
2. 再补 2021
3. 处理 2018-2020，并执行“连续3省搜不到即停该年份”

### A. 2022 年（优先）
- 已按缺失省份优先检索（in-en 站内优先 + 省级关键词）
- 本轮未新增可直接入库的 2022 省级“公共充电桩”数值（避免口径不一致/仅目标值数据入库）
- 2022 缺失维持：**16省**

### B. 2021 年（其次）
- 新增 2 条（均为缺失省份）：
  - 江苏：97,000（截至2021年12月）
  - 浙江：82,000（截至2021年12月）
- 来源：`https://finance.sina.com.cn/stock/resreport/2022-01-20/doc-ikyakumy1563680.shtml`

### C. 2018-2020（按停止规则）
- **2018**：在 in-en 检索到可用TOP10省份数据（截至2018年8月），新增 8 条：
  - 天津、河北、广东、江苏、山东、浙江、安徽、湖北
  - 来源：`https://chd.in-en.com/html/chd-2317718.shtml`
- **2019**：按省份顺序检索，连续3省未获得可入库数值后停止该年份
- **2020**：按省份顺序检索，连续3省未获得可入库数值后停止该年份

### 本轮数据与文件更新
- `charging_piles_by_province.csv/.xlsx`：**75 → 85（+10）**
- `source_registry.csv/.xlsx`：**36 → 38（+2）**
  - `SRC_CP_INEN_2018AUG_TOP10`
  - `SRC_CP_SINA_2021DEC_TOP5`
- `panel_with_charging_buses_30prov.csv/.xlsx` 已重跑合并

### 本轮QC
- `province+year` 唯一性：通过（重复=0）
- 面板 `public_charging_piles` 非空：**75 → 85**
- `public_charging_piles` 与 `public_charging_piles_source_id` 对齐：通过（不一致=0）

### 覆盖变化（2018-2022）
- 2018：缺失 **28 → 20**
- 2019：缺失 23（不变，已按规则停止）
- 2020：缺失 23（不变，已按规则停止）
- 2021：缺失 **25 → 23**
- 2022：缺失 16（不变）

---

## 本次继续执行：2022年剩余16省专项补缺（2026-03-24 深夜）

### 1) 执行策略（按要求）
- 对缺失省份逐省检索：
  - `{省名} 公共充电桩 2022 保有量 台`
  - `{省名} 充电基础设施 2022年底 万个`
  - `{省名} 发改委 充电桩 2022`
- 同步进行 `site:chd.in-en.com` 站内检索（省名+充电桩+2022）
- 仅入库“可核验文本数值”，其余留空

### 2) 本轮新增（2022）
- 新增 1 条：
  - 四川 2022：**42,000**
  - 依据：`https://www.sc.gov.cn/10462/10464/13298/13302/2022/4/25/35540a6804ff4c29ba7e726381bc29eb.shtml`
  - 原文口径：**“截至2022年3月，四川公共充电桩总量达到4.2万个”**

### 3) 本轮未入库说明
- 天津、河北、吉林、黑龙江、江西、湖南、广西、重庆、贵州、云南、陕西、甘肃、青海、宁夏、新疆：
  - 检索到的信息多为“充电桩总量（含私桩）/充电站数量/高速场景子集/目标值”，
  - 或虽有数字但不满足“2022口径公共充电桩可直接核验文本值”，故按规则暂不入库。

### 4) 文件更新
- `data_collector/output/charging_piles_by_province.csv/.xlsx`
- `data_collector/output/source_registry.csv/.xlsx`
- `merged_output/panel_with_charging_buses_30prov.csv/.xlsx`

### 5) 本轮QC
- 充电桩记录：**85 → 86（+1）**
- 面板 `public_charging_piles` 非空：**85 → 86**
- `province+year` 唯一性：通过（重复=0）
- `public_charging_piles` 与 `source_id` 对齐：通过（不一致=0）
- 2022本批16省缺口：**16 → 15**
