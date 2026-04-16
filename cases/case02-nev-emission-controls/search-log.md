# 搜索与采集日志（case02-nev-emission-controls）

更新时间：2026-03-26

## 1) NBS 指标确认（data.stats.gov.cn）
- 入口：`https://data.stats.gov.cn/easyquery.htm?cn=E0103`
- 反爬现象：直接 requests 可能返回 challenge HTML（非 JSON）
- 处理策略：
  - 解析 challenge 页面内 JS
  - 用 Node 执行 JS，得到下一跳 `WZWSREL...` URL
  - 多轮请求直到拿到 JSON

## 2) 指标代码
- `A020101` 地区生产总值（亿元）
- `A020104` 第三产业增加值（亿元）
- `A030101` 年末常住人口（万人）
- `A030102` 城镇人口（万人）
- `A0G0401` 旅客周转量（亿人公里）
- `A0G0601` 货物周转量（亿吨公里）
- `A0G0203` 公路里程（万公里）

## 3) 其他数据来源
- NEV 保有量：`math/data_collector/output/nev_stock_30prov_2012_2023.csv`
- 交通油耗：`math/merged_output/all_priorities_merged_panel_30prov_2012_2023.csv`

## 4) 构造与合并
- 统一省份命名为全称（30省）
- 统一年份范围 2012–2023
- 构造派生变量：
  - `gdp_per_capita_yuan`
  - `urbanization_rate`
  - `tertiary_share`
- 构造交通CO2估算：
  - `transport_co2_est_10k_ton = gasoline*2.925 + diesel*3.096`

## 5) 结果
- 最终面板：`data/panel_case02_30prov_2012_2023.csv`
- 覆盖率：核心 8 变量均为 360/360

## 6) 严格口径 NEV 补采（2026-03-25）
- 执行脚本：`python scripts/collect_case02_nev_strict_partial.py`
- 入库规则：仅接受省级官方站点中可直接定位“保有量”且可对应 2023 年末/年度存量的表述。
- 本轮确认：
  - 北京市（2023）：77.3 万辆  
    <https://fgw.beijing.gov.cn/gzdt/fgzs/mtbdx/bzwlxw/202408/t20240820_3777559.htm>
  - 甘肃省（2023）：9.7879 万辆（由97879辆换算）  
    <https://www.jingtai.gov.cn/zfxxgk/bmhxzxxgk/xzfzcbmzsjgml/xgaj/fdzdgknr/gsgg/art/2024/art_85e3c3c630264fbd9821d09e2249a038.html>
  - 贵州省（2023，截至12-22）：27.48 万辆  
    <https://drc.guizhou.gov.cn/xwzx/zwyw/202401/t20240112_83529665.html>
  - 浙江省（2023）：204 万辆  
    <https://www.zj.gov.cn/art/2024/1/26/art_1554467_60195319.html>
  - 上海市（2023）：128.8 万辆  
    <https://www.shanghai.gov.cn/nw4411/20240303/210a0336b8c14e97a6de2c0672d969fc.html>
  - 广东省（2023）：289 万辆  
    <http://www.gd.gov.cn/gdywdt/bmdt/content/post_4422331.html>
  - 重庆市（2023）：45 万辆  
    <https://www.cq.gov.cn/zwgk/zfxxgkml/zcjd_120614/mtsj/202405/t20240509_13189834.html>
- 产出文件：
  - `data/nev_stock_strict_2023_partial.csv`
  - `data/panel_case02_strict_30prov_2012_2023.csv`（对应省份 2023 行已写入）
  - `data/source_registry_strict.csv`（新增 4 条 A 级来源）

## 7) 严格口径 NEV 二轮补采（2026-03-26）
- 执行脚本：`python scripts/collect_case02_nev_strict_partial.py`
- 本轮新增入库（2023）：
  - 天津市：48 万辆（截至2023年底）  
    <https://www.tj.gov.cn/zmhd/wmfkxd/202408/t20240816_6700013.html>
  - 湖南省：56.50 万辆（2023年）  
    <https://tjj.hunan.gov.cn/hntj/tjfx/jmxx/2024sjjd/202409/t20240929_33465665.html>
  - 广西壮族自治区：92.37 万辆（截至11月底）  
    <http://www.gxzf.gov.cn/gxyw/t19439729.shtml>
  - 海南省：27.3 万辆（截至10月底）  
    <https://www.hainan.gov.cn/hainan/5309/202401/490e107fee4340c1aacb5edd1f841326.shtml>
- 当前严格覆盖：
  - `nev_stock_10k = 11/360`（2023 年覆盖 11 省）

## 8) 严格口径 NEV 三轮补采（2026-03-26）
- 执行脚本：`python scripts/collect_case02_nev_strict_partial.py`
- 本轮新增入库（2023）：
  - 安徽省：60.3 万辆（截至2023年11月底）  
    <https://fzggw.ah.gov.cn/public/7011/148994711.html>
- 当前严格覆盖：
  - `nev_stock_10k = 12/360`（2023 年覆盖 12 省）

## 9) 严格口径 NEV 四轮补采（2026-03-26）
- 执行脚本：`python scripts/collect_case02_nev_strict_partial.py`
- 本轮新增入库（2023）：
  - 山东省：165.9 万辆（截至2023年9月底）  
    <http://nyj.shandong.gov.cn/art/2023/12/2/art_59966_10301975.html>
  - 河北省：80.8 万辆（2023全年口径）  
    <https://gxt.hebei.gov.cn/hbgyhxxht/zfxxgk/fdzdgknr/gzdt68/tzgg9917/2025042121501226167/index.html>
  - 河南省：114 万辆（截至2023年底，电动汽车口径）  
    <https://hnjs.henan.gov.cn/2024/08-12/3035341.html>
  - 四川省：89.63 万辆（2023年底，电动汽车口径）  
    <https://www.sc.gov.cn/10462/10464/13298/13299/2024/6/28/08e35bde8718453d9a27934e8c9bea17.shtml>
- 当前严格覆盖：
  - `nev_stock_10k = 16/360`（2023 年覆盖 16 省）

## 10) 严格口径 NEV 五轮补采（2026-03-26，自动批量续跑）
- 执行脚本：`python scripts/collect_case02_nev_strict_partial.py`
- 本轮新增入库（2023）：
  - 云南省：32.6 万辆（截至2023年10月底）  
    <https://nyj.yn.gov.cn/nyj_file/html/xzgfwjjd/2024/1217/000027.html>
  - 宁夏回族自治区：4.3 万辆（截至2023年9月底）  
    <https://yinchuan.gov.cn/xwzx/mrdt/202311/t20231101_4335710.html>
- 稳定性改进（已写入脚本）：
  - 增加多轮重试与备用 URL 机制（减少 502/临时失败影响）
  - `nev_stock_strict_2023_partial.csv` 改为“增量合并写入”（避免单次失败导致已采集行丢失）
  - 自动输出 2023 覆盖汇总与缺失省份列表
- 当前严格覆盖：
  - `nev_stock_10k = 18/360`（2023 年覆盖 18 省）
  - 2023 仍缺 12 省：内蒙古自治区、吉林省、山西省、新疆维吾尔自治区、江苏省、江西省、湖北省、福建省、辽宁省、陕西省、青海省、黑龙江省
- 同轮自动检索（12省批量）结果：
  - 已执行官方域名批量检索与候选页扫描；
  - 未发现满足“省级口径 + 2023年可直接定位保有量数值 + 可复现抓取”的新增来源，故未入库新值。

## 11) Camoufox 搜索链路接入与第六轮补采（2026-03-26）
- 新增脚本（普通用户模式）：
  - `scripts/discover_case02_nev_camoufox.py`
  - 默认加载插件：`addons/fp_obfuscator_lite/`
- 运行方式示例：
  - `python scripts/discover_case02_nev_camoufox.py --output cases/case02-nev-emission-controls/tmp/camoufox_missing12_fast.json`
- 说明：使用 Camoufox + humanize + 指纹混淆插件进行搜索候选发现，再由严格脚本入库。
- 本轮新增入库（2023）：
  - 山西省：34.64 万辆（截至2023-08-07“截至目前”时点口径）  
    <http://www.shanxi.gov.cn/ywdt/sxyw/202308/t20230807_9078335.shtml>
- 当前严格覆盖：
  - `nev_stock_10k = 19/360`（2023 年覆盖 19 省）
  - 2023 仍缺 11 省：内蒙古自治区、吉林省、新疆维吾尔自治区、江苏省、江西省、湖北省、福建省、辽宁省、陕西省、青海省、黑龙江省

## 12) 严格口径 NEV 第七轮补采（2026-03-26）
- 执行脚本：`python scripts/collect_case02_nev_strict_partial.py`
- 本轮新增入库（2023）：
  - 内蒙古自治区：8.2998 万辆（截至2023-09-30，82998辆换算）  
    <http://kjj.bynr.gov.cn/kjxx/gnkj/202311/t20231114_574040_senior.html>
  - 陕西省：39.77 万辆（2023-08-11 时点，电动汽车口径）  
    <https://www.shaanxi.gov.cn/xw/sxyw/202308/t20230811_2296960_wap.html>
  - 新疆维吾尔自治区：5 万辆（2023-10-18 时点）  
    <https://www.xinjiang.gov.cn/xinjiang/bmdt/202310/2339a216530641b7adab3da6bd6bbe48.shtml>
- 当前严格覆盖：
  - `nev_stock_10k = 22/360`（2023 年覆盖 22 省）
  - 2023 仍缺 8 省：吉林省、江苏省、江西省、湖北省、福建省、辽宁省、青海省、黑龙江省

## 13) 严格口径 NEV 第八轮补采（2026-03-26）
- 执行脚本：`python scripts/collect_case02_nev_strict_partial.py`
- 本轮新增入库（2023）：
  - 江苏省：33.4 万辆（2023-01 时点，电动汽车口径）  
    <http://www.jszx.gov.cn/wylz/zxta/2023ta/202301/t20230116_94117.html>
- 同轮检索（Camoufox/Sogou + 官方站点候选复核）：
  - 已对吉林、江西、湖北、福建、辽宁、青海、黑龙江开展多轮候选扫描；
  - 发现大量全国口径或地市口径页面，但暂未确认“省级 + 2023 + 可直接提取数值”的新增来源。
- 当前严格覆盖：
  - `nev_stock_10k = 23/360`（2023 年覆盖 23 省）
  - 2023 仍缺 7 省：吉林省、江西省、湖北省、福建省、辽宁省、青海省、黑龙江省

## 14) 严格口径 NEV 第九轮续跑（2026-03-26，自动多轮检索）
- 目标：继续补齐剩余 7 省（吉林、江西、湖北、福建、辽宁、青海、黑龙江）。
- 已执行多轮检索（均写入 `cases/case02-nev-emission-controls/tmp/`）：
  - `camoufox_missing7_round17_headed.json`
  - `sogou_missing7_precise_round18.json`
  - `site_domain_scan_missing7_round19.json`
  - `jiangxi_search5_api_round20.json`（江西省站内 `search5/search/s` 接口批量翻页）
  - `hubei_site_query_round21.json`
  - `missing6_sitequery_round22.json`
- 结果：
  - 检出候选多为**全国口径**或**地市口径**（武汉、襄阳、沈阳、厦门等），以及**非2023时点**；
  - 暂未新增满足“省级 + 2023 + 原文可直接提取数值”的来源，故本轮不入库。
- 当前严格覆盖保持：
  - `nev_stock_10k = 23/360`（2023 年覆盖 23 省）
  - 2023 仍缺 7 省：吉林省、江西省、湖北省、福建省、辽宁省、青海省、黑龙江省

## 15) 严格口径 NEV 第十轮续跑（2026-03-26，Camoufox增强脚本）
- 脚本增强（`scripts/discover_case02_nev_camoufox.py`）：
  - 浏览器单实例复用（减少重复启动）；
  - 支持断点续跑（`--resume`）；
  - 支持搜索引擎顺序控制（`--engines sogou,360,bing`）；
  - URL正文抓取并发（`--fetch-workers`）；
  - 运行完成后写入结构化查询详情（每条 query 的 engine / anti 状态 / 命中数）。
- 本轮命令：
  - `python scripts/discover_case02_nev_camoufox.py --resume --run-mode headless --output cases/case02-nev-emission-controls/tmp/camoufox_missing7_v2.json --engines sogou,360,bing --max-pages 30 --max-candidates 12 --fetch-workers 8`
- 本轮检索摘要（剩余 7 省）：
  - 吉林省：urls=27，candidates=0
  - 江西省：urls=30，candidates=0
  - 湖北省：urls=30，candidates=0
  - 福建省：urls=30，candidates=2（候选为历史地市口径，未入库）
  - 辽宁省：urls=30，candidates=1（候选来源为地市转载，口径待否决）
  - 青海省：urls=16，candidates=1（候选年份为2019历史页面，未入库）
  - 黑龙江省：urls=23，candidates=0
- 入库结果：本轮 **无新增**（严格规则下不满足“省级 + 2023 + 可直接提取”）。
- 当前严格覆盖保持：
  - `nev_stock_10k = 23/360`（2023 年覆盖 23 省）
  - 2023 仍缺 7 省：吉林省、江西省、湖北省、福建省、辽宁省、青海省、黑龙江省

## 16) 工程化改进（2026-03-26）
- 目标：解决“搜索慢 / 临时文件散落 / 需要人工逐轮继续”问题。
- 已完成：
  1. `discover_case02_nev_camoufox.py` 增强
     - 新增 `--max-fetch-pages`（抓取正文上限，默认20）；
     - 新增 URL 预打分（优先抓取更相关页面）；
     - 新增正文缓存（同URL多次命中仅抓取一次）；
     - 新增 `--request-timeout-sec` / `--query-timeout-ms`；
     - 输出 `url_count_raw` / `fetch_count` 便于耗时诊断。
  2. 新增全自动入口：`scripts/run_case02_nev_strict_autopilot.py`
     - 一条命令执行：刷新 strict 面板 → 缺口省份自动检索多轮 → 产出状态报告；
     - 无需逐轮对话“继续”。
  3. 临时文件归档
     - 仓库根目录历史 `_tmp_* / tmp_*` 已统一迁移到 `tmp/legacy/`；
     - `.gitignore` 新增 `_tmp_*`、`tmp_*`、`tmp/`、`cases/**/tmp/` 规则，避免再次散落。

## 17) 高级多引擎配置（2026-03-27）
- 按“通用数据搜集框架”方向，补充了高级搜索能力：
  - `discover_case02_nev_camoufox.py` 支持引擎：`google`、`tavily`（并保留 `sogou/360/bing`）；
  - 新增 `--config`（JSON/TOML）配置文件加载；
  - 新增 `--domain-filter`（支持非 `gov.cn` 任务场景）；
  - 新增 Tavily 参数：`--tavily-api-key`、`--tavily-endpoint`、`--tavily-max-results`、`--tavily-topic`；
  - 新增 Google 参数：`--google-max-results`、`--google-hl`、`--google-gl`。
- 新增模板配置：
  - `templates/advanced-search-config.example.toml`
- 自动续跑脚本同步透传高级参数：
  - `run_case02_nev_strict_autopilot.py` 新增 `--discover-config` 与 Tavily/Google 参数透传。

## 18) MCP 搜索层补充（2026-03-27）
- 新增 MCP 自检脚本：
  - `scripts/check_mcp_servers.py`
  - 用于检查本地 MCP 客户端配置中是否已配置 `tavily-proxy`、`exa-proxy`。
- 新增模板：
  - `templates/mcp-servers.example.toml`
- 本机检查结果（当次）：`tavily-proxy` 已配置，`exa-proxy` 缺失（需按模板补充）。

## 19) 数据处理分层补充（2026-03-27）
- 按“发现-归档-抽取”分层处理思路，新增：
  - `scripts/process_web_data_pipeline.py`
  - `templates/extraction-schema-template.json`
- 能力：
  1. URL 页面内容 markdown-like 归档（可审计）；
  2. schema 规则抽取（结构化字段 + evidence）；
  3. 输出 `pages_summary.csv` + `pages_markdown.jsonl` + `pages_extracted.jsonl`。

## 20) 自动续跑接入处理层（2026-03-27）
- 已将 `process_web_data_pipeline.py` 接入 `run_case02_nev_strict_autopilot.py`：
  - discover 后默认执行处理层；
  - 每轮输出 `tmp/autopilot/processed_roundN/`；
  - 新增参数：`--skip-processing`、`--process-mode`、`--process-schema-file`、`--process-max-urls` 等。

## 21) Planner 路由层补充（2026-03-27）
- 采用“先规划后执行”的任务路由方式：
  - 新增 `scripts/plan_research_workflow.py`
  - 新增 `templates/research-spec-template.json`
- 能力：
  - 自动将变量清单路由到 API / 浏览器 / 文档执行器；
  - 输出 `.plan.json` + `.plan.md`，作为自动化搜集的上游任务单。

## 22) Agent Hub 接入 Planner API（2026-03-27）
- `scripts/agent_hub.py` 新增：
  - API端点：`POST /plan-workflow`
  - 交互命令：`plan_workflow --spec-file ...`
- 作用：将“规划层（Planner）”并入现有 API+交互 Agent 流程。

## 23) Agent Hub 一体化编排端点（2026-03-27）
- 新增 `POST /plan-auto-rounds`：
  - 先执行 `plan_research_workflow.py`
  - 再执行 `run_auto_rounds.py`
- 交互模式新增命令：`plan_auto_rounds ...`

## 24) 稳定性与可重复性改进（2026-03-27）
- `discover_case02_nev_camoufox.py` 输出补充：
  - `selected_urls`
  - `selected_url_meta`
  便于后续处理层直接使用更多URL，而不是只依赖 top_candidates。
- `process_web_data_pipeline.py` 默认改为覆盖写（避免重复累积），可用 `--append` 开启追加。
- `run_case02_nev_strict_autopilot.py` 新增 `--fresh-output`，支持清空 autopilot 历史产物后重跑。
