# 如何用 AI Agent 协作采集数据

## 常见 Agent 类型

| 类型 | 优势 | 适合的阶段 |
|------|------|-----------|
| **浏览器执行型 Agent** | 联网搜索、逐页检索、批量操作 | 搜索候选、逐省逐年补缺 |
| **长文本理解型 Agent** | 阅读长文、整理字段、总结口径 | 分析搜索结果、提取数字 |
| **本地脚本执行型 Agent** | 调用命令、处理文件、跑校验 | 合并结果、跑 QC、导出交付物 |

## 核心原则

### 1. 先给规范，再让搜索

❌ 错误做法：
```
"帮我搜各省充电桩数据"
```

✅ 正确做法：给标准化任务文档（见 [task-spec-template.md](../templates/task-spec-template.md)），包含：
- 变量定义和口径
- 搜索关键词模板
- 输出CSV格式
- 来源分级规则
- 红线约束（禁止估算）

### 2. 分批给任务

❌ 一次给全部8年30省
✅ 一次给1-2年，做完汇报再继续

### 3. 要求统一汇报格式

每轮让AI汇报：
```markdown
### 本轮结果
- 新增 X 条数据
- 来源：[URLs]
- QC：province+year 重复=0
- 覆盖变化：YYYY年缺失 N→M 省
```

## 推荐协作模式

```
┌─── 任务组织层 ───┐     ┌──── 执行层 ────┐
│ 1.定义变量与口径  │     │                │
│ 2.准备任务文档    │────→│ 3.按文档系统搜索 │
│ 4.审查结果与补充  │←────│ 5.汇报与记录    │
│ 6.合并去重入库    │     │                │
└─────────────────┘     └───────────────┘
```

### 给 Agent 的任务要点

1. **先给进度文件路径**（让它知道已有哪些数据）
2. **给明确的停止条件**（如"连续3省搜不到就停"）
3. **要求它更新进度文件**（而不是只在对话中回复）
4. **强调红线**（禁止估算、必须有URL）

### 示例任务

```
请阅读 d:\path\to\进度汇报.md 获取当前进度。

继续执行充电桩数据补充，专攻2022年缺失省份。策略：
1. 优先搜索A/B级来源
2. 逐省搜索："{省名} 公共充电桩 2022 保有量 台"
3. 连续3省搜不到即停止
4. 新数据追加到CSV，跑合并+QC
5. 更新进度汇报文件
```

## 常见坑

| 坑 | 应对 |
|----|------|
| AI编造数据 | 要求每条附URL，抽查验证 |
| 口径搞混（新增vs保有） | 在任务文档中用❌明确禁止 |
| 单位换算错 | 要求在note中注明原始单位 |
| 重复入库 | QC脚本检查 province+year 唯一 |
| 来源过时/失效 | 记录access_date，及时存证 |

## 高级用户：多引擎混合搜索

- 推荐引擎顺序：`google,tavily,bing,sogou,360`
- Tavily 使用环境变量：`TAVILY_API_KEY`
- 用配置文件统一管理高级参数（见 `templates/advanced-search-config.example.toml`）
- MCP 建议同时配置：`tavily-proxy` + `exa-proxy`（可用 `python scripts/check_mcp_servers.py` 自检）

示例：

```bash
set TAVILY_API_KEY=your_key_here
python cases/case02-nev-emission-controls/scripts/discover_case02_nev_camoufox.py --config templates/advanced-search-config.example.toml --engines google,tavily,bing,sogou,360
```

## 处理分层建议

- 第1层：采集候选 URL（搜索）
- 第2层：网页内容归档（markdown-like）
- 第3层：按 schema 提取结构化字段（含 evidence）

本仓库对应脚本：

```bash
python scripts/process_web_data_pipeline.py \
  --input-json cases/case02-nev-emission-controls/tmp/camoufox_missing7_v2.json \
  --schema-file templates/extraction-schema-template.json \
  --output-dir cases/case02-nev-emission-controls/tmp/processed \
  --mode both
```

## Planner 先行

先做任务拆解与路由，再执行搜索：

```bash
python scripts/plan_research_workflow.py --spec-file templates/research-spec-template.json
```

如果走 API 进程，也可直接调用：

```bash
POST /plan-workflow
{
  "spec_file": "templates/research-spec-template.json"
}
```

也可直接走一体化接口（Planner -> AutoRounds）：

```bash
POST /plan-auto-rounds
{
  "spec_file": "templates/research-spec-template.json",
  "data": "cases/case01-nev-carbon/data/charging_piles_by_province.csv",
  "value_col": "public_charging_piles",
  "year_start": 2017,
  "year_end": 2023
}
```
