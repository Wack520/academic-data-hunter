# 逐年搜集分省数据任务（供 Agent 执行）- v2（可审计版）

## 任务目标

搜集两类分省面板数据，**每个数据点必须有真实来源URL与证据文件**，禁止任何估算/推算/插值：

1. **各省公共充电桩保有量**（台）— 30省 × 2016-2023
2. **各省新能源公交车数量**（辆）— 30省 × 2012-2023

最终输出统一保存到当前案例目录：`cases/case01-nev-carbon/data/`。

---

## 30省列表（剔除西藏及港澳台）

```
北京, 天津, 河北, 山西, 内蒙古, 辽宁, 吉林, 黑龙江,
上海, 江苏, 浙江, 安徽, 福建, 江西, 山东, 河南,
湖北, 湖南, 广东, 广西, 海南, 重庆, 四川, 贵州,
云南, 陕西, 甘肃, 青海, 宁夏, 新疆
```

---

## 来源分级与使用规则（重要）

> 你说得对：媒体来源一般也有参考价值。**本方案允许媒体来源**，但要分级管理。

- **A级（优先入库）**：政府/部委/省厅官网、统计年鉴原表、官方数据库
- **B级（可入库）**：行业协会/联盟官方发布（如EVCIPA）
- **C级（条件入库）**：媒体、研究机构、转载站点

### C级来源使用条件（必须同时满足）
1. 标注 `source_level = C`
2. 提供至少 1 个独立交叉来源（`cross_check_url`）
3. 明确“原始出处是否可追溯”（如“转引自EVCIPA月报”）
4. 若与A级/B级冲突，以A级/B级为准

---

## 任务一：各省公共充电桩保有量（2016-2023）

### 口径固定
- 指标：`public_charging_piles`
- 单位：**台**
- 时间口径：**年末保有量**（禁止使用“新增量”替代）

### 搜集流程
1. 年份循环（2016-2023）
2. 先查 A/B 级来源（EVCIPA、省级发改/能源主管部门、国家能源相关发布）
3. 不足部分再用 C 级来源补充（必须满足C级条件）
4. 每条数据必须记录来源链

### 搜索关键词模板
```
"{YEAR}年 各省 公共充电桩 保有量"
"{YEAR}年 中国充电联盟 公共充电桩 分省"
"{YEAR}年 充电基础设施 运行情况 省"
"{PROVINCE} {YEAR} 充电桩 保有量"
```

### 输出文件
`cases/case01-nev-carbon/data/charging_piles_by_province.csv`

字段：
- `province, year, public_charging_piles`
- `source_id, source_name, source_level, source_url, cross_check_url`
- `publish_date, access_date, evidence_file`
- `note`

---

## 任务二：各省新能源公交车数量（2012-2023）

### 口径固定
- 指标：`nev_buses`
- 单位：**辆**
- 时间口径：**年末保有量**
- 类型：`data_type` ∈ {`新能源(含混动)`, `纯电动`, `未说明`}

### 搜集流程
1. 年份循环（2012-2023）
2. 优先省级交通运输厅统计公报/统计年鉴（A级）
3. 其次行业协会/联盟官方报告（B级）
4. 最后媒体补充（C级，需交叉核验）

### 搜索关键词模板
```
"{YEAR}年 各省 新能源公交车 数量"
"{PROVINCE} 交通运输发展统计公报 {YEAR} 新能源公交"
"{YEAR}年 公共汽电车 纯电动 分省"
```

### 输出文件
`cases/case01-nev-carbon/data/nev_buses_by_province.csv`

字段：
- `province, year, nev_buses, data_type`
- `source_id, source_name, source_level, source_url, cross_check_url`
- `publish_date, access_date, evidence_file`
- `note`

---

## 任务三：来源台账（必须独立保存）

输出：`cases/case01-nev-carbon/data/source_registry.csv`

字段建议：
- `source_id`（唯一）
- `variable`（charging / nev_buses）
- `source_level`
- `source_name`
- `source_url`
- `cross_check_url`
- `publish_date`
- `access_date`
- `evidence_file`
- `is_primary`（是否原始发布）

---

## 任务四：合并到主面板

合并时不仅合并数值，还要合并来源ID：
- `public_charging_piles`, `public_charging_piles_source_id`
- `nev_buses`, `nev_buses_source_id`
- `nev_buses_data_type`

输出：
`cases/case01-nev-carbon/data/panel_30prov_2012_2023.csv`

---

## 质量控制（QC）

1. **唯一性检查**：每个文件 `province+year` 唯一
2. **单位检查**：全部转为“台/辆”，禁止“万台/万辆”直接入库
3. **口径检查**：剔除“新增量”误填
4. **来源检查**：每条非空值必须有 `source_id`
5. **可信度检查**：C级来源必须有 `cross_check_url`
6. **缺失处理**：搜不到就留空，不填补

---

## AI使用边界

- ✅ 可用：检索链接、解析网页、抽取文本、整理台账
- ❌ 禁止：生成数值、猜测缺失值、插值外推

---

## 执行顺序

1. 先做公共充电桩（2016-2023）
2. 再做新能源公交车（2012-2023）
3. 生成来源台账
4. 合并主面板并跑QC

---

## 关键约束（红线）

- ❌ 禁止估算/推算/插值/外推
- ❌ 禁止无URL来源数据入库
- ✅ 允许媒体来源，但必须分级+交叉核验
- ✅ 每个数字可追溯到URL与证据文件
- ✅ 搜不到就留空，诚实标记缺失
