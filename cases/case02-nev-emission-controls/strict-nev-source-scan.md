# NEV 严格口径来源扫描（2026-03-26）

## 目标
为 `nev_stock_10k` 寻找可复现、可审计、官方口径的 **30省 × 2012-2023** 分省年度数据源。

## 已核查来源

### 1) 国家统计局国家数据（NBS）
- 入口：<https://data.stats.gov.cn/easyquery.htm?cn=E0103>
- 指标树扫描结果（2026-03-25）：
  - 分省年度库 `fsnd`：交通相关可见 `A0G07/08/09/0A`（民用汽车/私人汽车等），但未发现“新能源汽车保有量”指标代码。
  - 月度/季度库 `hgyd`、`hgjd`：可见“新能源汽车”相关代码，但不满足“分省年度保有量”口径。
- 结论：**未发现可直接拉取 30省×2012-2023 新能源汽车保有量的统一官方API口径**。

### 2) CEADs
- 入口：<https://www.ceads.net.cn/data/province/>
- 已用于交通碳排放分部门清单下载（2012-2022）。
- 结论：CEADs 不提供 NEV 保有量变量。

## 当前判断（严格口径）
- 统一单一官方数据源暂不可得。
- 可执行的严格路线：改为 **省级官方公报/统计年鉴逐省逐年采集**，仅录入有原文证据的数据，缺失留空，不插值、不外推。

## 已确认入库（2023，严格口径）
- 北京市：77.3 万辆  
  <https://fgw.beijing.gov.cn/gzdt/fgzs/mtbdx/bzwlxw/202408/t20240820_3777559.htm>
- 甘肃省：9.7879 万辆（由 97879 辆换算）  
  <https://www.jingtai.gov.cn/zfxxgk/bmhxzxxgk/xzfzcbmzsjgml/xgaj/fdzdgknr/gsgg/art/2024/art_85e3c3c630264fbd9821d09e2249a038.html>
- 贵州省：27.48 万辆（截至2023-12-22）  
  <https://drc.guizhou.gov.cn/xwzx/zwyw/202401/t20240112_83529665.html>
- 浙江省：204 万辆  
  <https://www.zj.gov.cn/art/2024/1/26/art_1554467_60195319.html>
- 上海市：128.8 万辆  
  <https://www.shanghai.gov.cn/nw4411/20240303/210a0336b8c14e97a6de2c0672d969fc.html>
- 广东省：289 万辆  
  <http://www.gd.gov.cn/gdywdt/bmdt/content/post_4422331.html>
- 重庆市：45 万辆  
  <https://www.cq.gov.cn/zwgk/zfxxgkml/zcjd_120614/mtsj/202405/t20240509_13189834.html>

当前严格面板覆盖：`nev_stock_10k = 7/360`（仅上述 7 省 2023 年）。

## 追加入库（2026-03-26）
- 天津市：48 万辆（截至2023年底）  
  <https://www.tj.gov.cn/zmhd/wmfkxd/202408/t20240816_6700013.html>
- 湖南省：56.50 万辆（2023年）  
  <https://tjj.hunan.gov.cn/hntj/tjfx/jmxx/2024sjjd/202409/t20240929_33465665.html>
- 广西壮族自治区：92.37 万辆（截至2023年11月底）  
  <http://www.gxzf.gov.cn/gxyw/t19439729.shtml>
- 海南省：27.3 万辆（截至2023年10月底）  
  <https://www.hainan.gov.cn/hainan/5309/202401/490e107fee4340c1aacb5edd1f841326.shtml>

当前严格面板覆盖更新：`nev_stock_10k = 11/360`。

## 追加入库（2026-03-26，第3轮）
- 安徽省：60.3 万辆（截至2023年11月底）  
  <https://fzggw.ah.gov.cn/public/7011/148994711.html>

当前严格面板覆盖更新：`nev_stock_10k = 12/360`。

## 追加入库（2026-03-26，第4轮）
- 山东省：165.9 万辆（截至2023年9月底）  
  <http://nyj.shandong.gov.cn/art/2023/12/2/art_59966_10301975.html>
- 河北省：80.8 万辆（2023全年口径）  
  <https://gxt.hebei.gov.cn/hbgyhxxht/zfxxgk/fdzdgknr/gzdt68/tzgg9917/2025042121501226167/index.html>
- 河南省：114 万辆（截至2023年底，电动汽车口径）  
  <https://hnjs.henan.gov.cn/2024/08-12/3035341.html>
- 四川省：89.63 万辆（2023年底，电动汽车口径）  
  <https://www.sc.gov.cn/10462/10464/13298/13299/2024/6/28/08e35bde8718453d9a27934e8c9bea17.shtml>

当前严格面板覆盖更新：`nev_stock_10k = 16/360`（2023年覆盖16省）。

## 追加入库（2026-03-26，第5轮自动续跑）
- 云南省：32.6 万辆（截至2023年10月底）  
  <https://nyj.yn.gov.cn/nyj_file/html/xzgfwjjd/2024/1217/000027.html>
- 宁夏回族自治区：4.3 万辆（截至2023年9月底）  
  <https://yinchuan.gov.cn/xwzx/mrdt/202311/t20231101_4335710.html>

当前严格面板覆盖更新：`nev_stock_10k = 18/360`（2023年覆盖18省）。

## 当前缺口（2023）
- 吉林省、江西省、湖北省、福建省、辽宁省、青海省、黑龙江省

> 说明：上述缺口并非未检索，而是尚未找到“可复现抓取 + 官方原文直接给出2023省级保有量”的页面；按严格规则继续留空。

## 追加入库（2026-03-26，第6轮）
- 山西省：34.64 万辆（截至目前，发布日期 2023-08-07）  
  <http://www.shanxi.gov.cn/ywdt/sxyw/202308/t20230807_9078335.shtml>

当前严格面板覆盖更新：`nev_stock_10k = 19/360`（2023年覆盖19省）。

## 追加入库（2026-03-26，第7轮）
- 内蒙古自治区：8.2998 万辆（截至2023年9月30日，82998辆换算）  
  <http://kjj.bynr.gov.cn/kjxx/gnkj/202311/t20231114_574040_senior.html>
- 陕西省：39.77 万辆（2023年内时点，电动汽车口径）  
  <https://www.shaanxi.gov.cn/xw/sxyw/202308/t20230811_2296960_wap.html>
- 新疆维吾尔自治区：5 万辆（2023年内时点）  
  <https://www.xinjiang.gov.cn/xinjiang/bmdt/202310/2339a216530641b7adab3da6bd6bbe48.shtml>

当前严格面板覆盖更新：`nev_stock_10k = 22/360`（2023年覆盖22省）。

## 追加入库（2026-03-26，第8轮）
- 江苏省：33.4 万辆（2023年年初时点，电动汽车口径）  
  <http://www.jszx.gov.cn/wylz/zxta/2023ta/202301/t20230116_94117.html>

当前严格面板覆盖更新：`nev_stock_10k = 23/360`（2023年覆盖23省）。

## 第8轮并行检索结论（未入库）
- 已对吉林、江西、湖北、福建、辽宁、青海、黑龙江开展 Camoufox + 搜索引擎多轮扫描与页面复核。
- 高命中候选以全国口径、地市口径、或 2024/2025 时点为主；截至本轮，未确认新的“省级+2023+原文可直接提取数值”来源。

## 第9轮续跑结论（2026-03-26，未入库）
- 执行了面向剩余 7 省的自动多轮检索与复核，含：
  - Camoufox 批量发现；
  - Sogou 精确 query（`site:domain + 保有量`）；
  - 江西省站内 `search5/search/s` API 批量翻页检索。
- 产出检索文件（`tmp/`）：
  - `camoufox_missing7_round17_headed.json`
  - `sogou_missing7_precise_round18.json`
  - `site_domain_scan_missing7_round19.json`
  - `jiangxi_search5_api_round20.json`
  - `hubei_site_query_round21.json`
  - `missing6_sitequery_round22.json`
- 结论：候选页面仍以全国口径/地市口径/非2023时点为主，暂无可新增入库的省级2023口径数据。

## 第10轮续跑结论（2026-03-26，Camoufox增强脚本，未入库）
- 增强脚本：`scripts/discover_case02_nev_camoufox.py`
  - 单实例浏览器复用
  - `--resume` 断点续跑
  - `--engines` 可配置搜索顺序
  - `--fetch-workers` 并发抓取候选正文
- 本轮输出：`tmp/camoufox_missing7_v2.json`
- 检索摘要：
  - 吉林/江西/湖北/黑龙江：未检出候选句；
  - 福建：检出 2 条历史地市口径（2022年泉州），不满足省级2023；
  - 辽宁：检出 1 条地市转载页，存在口径风险，不入库；
  - 青海：检出 1 条 2019 年历史页面，不入库。
- 结论：仍未新增满足“省级 + 2023 + 原文可直接提取数值”的来源，严格面板维持 `23/360`。

## 状态快照脚本
- 新增：`scripts/report_case02_nev_strict_status.py`
- 用途：一键生成当前覆盖率 + 缺失省份 + 候选摘要
- 示例：
  - `python scripts/report_case02_nev_strict_status.py --candidates cases/case02-nev-emission-controls/tmp/camoufox_missing7_v2.json --output cases/case02-nev-emission-controls/strict-nev-status.md`

## Camoufox 适配
- 新增候选搜索脚本：`scripts/discover_case02_nev_camoufox.py`
- 运行特性：Camoufox 普通用户模式 + humanize + 插件 `addons/fp_obfuscator_lite`
- 目标：在严格口径前提下，提高可抓取官方来源发现率（仅候选发现，不直接入库）。

## 下一步采集策略
1. 省统计局《国民经济和社会发展统计公报》（优先）
2. 省公安厅/交管局“机动车保有量”公告（次优，需核验口径）
3. 省统计年鉴正式表格（可下载Excel/PDF）

> 规则：仅接受 gov.cn 或省级统计/公安官方站点；每条数据必须有 URL + 原文摘录位置 + 单位换算说明。
