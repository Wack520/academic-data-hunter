# 来源分级规则

## 三级分类

### A级 — 政府与官方统计（优先入库）

- 国家统计局官网 (data.stats.gov.cn)
- 各省/市人民政府官网 (.gov.cn)
- 统计年鉴原表
- 部委统计公报（交通运输部、国家能源局等）
- 官方数据库（CEADs等学术数据库）

**入库条件**：直接入库，`source_level = A`

### B级 — 行业协会与官方联盟（可入库）

- 中国充电联盟 (EVCIPA)
- 中国汽车工业协会 (CAAM)
- 中国电力企业联合会
- 其他国家级行业协会的官方发布

**入库条件**：直接入库，`source_level = B`

### C级 — 媒体与研究机构（条件入库）

- 新闻门户（新浪、网易、人民网转载等）
- 研究机构报告（头豹、前瞻、智研等）
- 行业网站（国际能源网、北极星等）
- 证券研报

**入库条件**（必须同时满足）：
1. 标注 `source_level = C`
2. 提供至少1个交叉来源 (`cross_check_url`)
3. 标明原始出处（如"转引自EVCIPA月报"）
4. 若与A/B级冲突，以A/B级为准

## 优先级规则

同一省份同一年份有多个来源时：
```
A级 > B级 > C级
```
如果同级别有多个来源，取数值更接近的（或更新的）。

## 来源台账字段

```csv
source_id,variable,source_level,source_name,source_url,
cross_check_url,publish_date,access_date,is_primary
```
