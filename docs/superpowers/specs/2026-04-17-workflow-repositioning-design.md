# 公开数据采集与交付工作流框架重构设计

## 1. 背景

当前仓库已经具备一批真实案例、来源登记、Evidence Pack、Benchmark Eval、MCP 接入等能力，但公开叙事仍然明显受现有 `cases/` 目录影响，容易让新用户把项目理解为：

- 主要面向中国场景的数据案例集合；
- 主要围绕少数已有案例类型展开；
- 更像若干脚本与样例，而不是一套可迁移的 workflow。

这会直接限制项目的边界感、可扩展性、对真实用户的吸引力，以及作为求职作品时的专业形象。

本次重构的目标，不是先做大规模代码重写，而是先把项目身份、文档结构、示例组织方式，统一到“workflow-first”的方向上。

---

## 2. 新定位

### 2.1 主定位

**公开数据采集与交付工作流框架**

### 2.2 一句话说明

**从公开来源检索、抽取、校验并交付可复核数据资产。**

### 2.3 双入口说明

项目同时服务两类用户：

1. **研究 / 论文 / 建模 / 分析用户**
   - 需要把公开数据搜集任务做成可复核、可交接、可继续分析的数据资产。
2. **Agent / MCP / 自动化工作流开发者**
   - 需要把公开数据 workflow 作为外部系统的数据层、证据层与评估层接入。

### 2.4 边界说明

项目未来不以某一类案例、某一语言或某一国家的数据任务自我定义，而以 workflow 能力自我定义：

- 支持不同公开来源类型；
- 支持不同地区与语言的任务扩展；
- 以“公开、可验证、高质量来源优先”为统一原则；
- 以 Evidence Pack、来源台账、质量校验和量化评估作为统一交付标准。

---

## 3. 重构目标

本次重构聚焦以下 5 个结果：

1. **README 改成 workflow-first 主叙事**；
2. **docs 从 case 导向改成能力导向**；
3. **`cases/` 降级为示例概念，不再代表项目边界**；
4. **为后续 `examples/` 目录迁移准备统一结构与命名原则**；
5. **为新增全球公共统计样板与论文附录抽取样板预留叙事位置**。

非目标：

- 当前阶段不追求大规模重写核心脚本实现；
- 当前阶段不立即更改 repo 名；
- 当前阶段不要求所有旧示例一次性完成目录迁移。

---

## 4. README 设计

README 应采用“先 workflow，后能力，再 examples”的结构。

### 4.1 首页主结构

建议使用以下结构：

1. **主标题**：公开数据采集与交付工作流框架  
2. **副标题**：从公开来源检索、抽取、校验并交付可复核数据资产。  
3. **双入口说明**：既可用于研究与分析，也可作为 Agent / MCP 工作流的数据层接入。  
4. **这是什么**：解释项目不是单次搜索结果、不是只输出 CSV、不是只服务某几个案例，而是一整条 workflow。  
5. **workflow 能力清单**：任务定义、来源检索、结构化抽取、来源登记、数据校验、Evidence Pack、Benchmark Eval。  
6. **最终交付物**：明确展示 `dataset.csv / source_registry.csv / evidence_records.jsonl / evidence pack / benchmark eval`。  
7. **双入口使用视角**：研究用户、开发者 / Agent 用户。  
8. **examples 说明**：示例只是 workflow 的证明材料，不代表项目边界。  

### 4.2 README 应避免的旧问题

- 过度围绕中国区域面板案例展开；
- 让 `cases/` 成为第一叙事中心；
- 先堆 feature 名，再让读者自己猜整体 workflow；
- 用太多“不是 xxx”的表述替代正向定义。

---

## 5. docs 设计

### 5.1 设计原则

`docs/` 必须讲“workflow 能力”，而不是讲“现有示例题材”。

文档不应默认：

- 中国场景；
- 中文搜索；
- 某一类统计数据；
- 某几个现有案例。

文档应回答：

- 这个 workflow 是什么；
- 它的输入、过程、输出分别是什么；
- 来源如何分级；
- 如何做抽取、校验、交付与评估；
- 如何接入 Agent / MCP / 自动化系统；
- 示例在哪里，以及示例只是能力证明。

#### 5.2 目标文档结构

```text
docs/
  overview.md
  workflow.md
  researcher-guide.md
  developer-guide.md
  source-policy.md
  validation.md
  evidence-pack.md
  benchmark-eval.md
  integrations-mcp.md
  examples.md
  roadmap.md
```

#### 5.3 各文档职责

- `overview.md`：项目总览、适用对象、最终交付物；
- `workflow.md`：完整 workflow，从 task spec 到 benchmark eval；
- `researcher-guide.md`：研究/分析用户如何组织任务、验收交付物；
- `developer-guide.md`：CLI / API / MCP / Agent 用户如何接入；
- `source-policy.md`：来源等级、优先级、弱来源入库条件、cross-check 规则；
- `validation.md`：字段完整性、单位一致性、去重、台账匹配、口径检查；
- `evidence-pack.md`：为什么不是只给 CSV、交付包结构与复核方法；
- `benchmark-eval.md`：指标设计、分数意义、当前评估边界；
- `integrations-mcp.md`：本地接入方式与推荐调用入口；
- `examples.md`：示例索引，并明确 examples 不代表项目边界；
- `roadmap.md`：后续扩展方向。

#### 5.4 现有文档处理策略

#### 合并或吸收

以下文档的主要内容应被新结构吸收：

- `docs/showcase.md`
- `docs/use-cases.md`
- `docs/positioning.md`

#### 保留并重写

以下文档继续保留，但内容风格与结构需统一到新叙事：

- `docs/evidence-pack.md`
- `docs/benchmark-evals.md`（建议同步调整命名）
- `docs/mcp-server.md`（建议迁移为 `docs/integrations-mcp.md`）
- `docs/roadmap.md`

---

## 6. 示例目录设计

### 6.1 总原则

示例的职责是：

> 证明 workflow 可以落到不同类型的公开数据任务上。

示例不应承担“定义项目边界”的职责。

### 6.2 迁移策略

建议采用**分阶段迁移**：

#### 第一阶段

先在 README 和 docs 中把 `cases` 明确降级为“示例目录”。

#### 第二阶段

再做实际目录迁移：

```text
cases/ -> examples/
```

#### 第三阶段

补充新的非中国样板，让新目录命名和新叙事真正站稳。

### 6.3 目标结构

```text
examples/
  china-regional-panel/
  global-public-stats/
  paper-appendix-extraction/
```

### 6.4 命名原则

- 按任务类型命名；
- 不按 `case01/case02/case03` 这类编号命名；
- 不让私人实验编号成为公开仓库结构；
- 不让单一示例看起来像项目的唯一定义。

### 6.5 现有示例的归位策略

现有三个中国场景示例，可先统一视为 `china-regional-panel` 体系下的示例资产，而不是继续以三个彼此平级的公开“项目身份”存在。

### 6.6 每个示例目录的统一结构

```text
examples/<example-name>/
  README.md
  task-spec.md
  data/
  outputs/
  evidence-pack/
  benchmark/
  notes/
```

统一结构至少要覆盖：

- 任务定义；
- 数据结果；
- 来源台账；
- 交付包；
- 评估结果。

---

## 7. 新 example 设计

### 7.1 全球公共统计样板

#### 目录建议

```text
examples/global-public-stats/
```

#### 样板目标

证明 workflow 不局限于中国区域案例，而可直接迁移到国际公共统计任务。

#### 推荐来源

- World Bank
- UN
- OECD
- Eurostat

#### 推荐字段

- country
- year
- GDP
- population
- inflation
- CO2
- energy use
- urbanization

#### 推荐交付物

- dataset
- source registry
- evidence pack
- benchmark eval

### 7.2 论文附录抽取样板

#### 目录建议

```text
examples/paper-appendix-extraction/
```

#### 样板目标

证明 workflow 不只适用于结构化公共统计库，也适用于论文附录、表格和半结构化来源抽取。

#### 推荐交付物

与其他示例保持一致：

- task spec
- dataset
- provenance / evidence
- validation result
- benchmark result

---

## 8. 执行顺序

### Phase 1：叙事重构

先完成：

- README 重写；
- docs 能力化重组；
- 在文档中把 `cases` 降级成 examples 概念；
- roadmap 与导航入口统一到新定位。

### Phase 2：结构重构

再完成：

- `cases/` 到 `examples/` 的正式迁移；
- 示例命名去编号化；
- 示例目录结构标准化；
- 示例 README 统一改成“workflow 示例说明”。

### Phase 3：能力证明

再补：

- `examples/global-public-stats/`
- `examples/paper-appendix-extraction/`

### Phase 4：品牌升级

最后再考虑：

- repo 名是否更改；
- 对外品牌名是否需要调整；
- 发布节奏与对外展示策略。

---

## 9. 第一批应修改的文件

### 第一批立即修改

- `README.md`
- `docs/evidence-pack.md`
- `docs/benchmark-evals.md` 或重命名后的对应文档
- `docs/mcp-server.md` 或迁移后的 `docs/integrations-mcp.md`
- `docs/roadmap.md`
- 新增：
  - `docs/overview.md`
  - `docs/workflow.md`
  - `docs/researcher-guide.md`
  - `docs/developer-guide.md`
  - `docs/source-policy.md`
  - `docs/validation.md`
  - `docs/examples.md`

### 第二批再修改

- `cases/` 的路径与目录名；
- 各示例 README；
- examples 索引与跳转关系。

### 当前阶段不建议大动的部分

- 核心脚本逻辑；
- 主要测试结构；
- CI 主流程；
- 现有 data 本体。

理由：当前第一目标是“改项目身份”，不是“先做底层大手术”。

---

## 10. 验收标准

重构完成后，新用户进入仓库应能快速理解：

### 这不是

- 一个中国数据案例仓库；
- 一个只会网页搜索的小工具；
- 一个纯粹只服务 Agent 的内部脚本集合。

### 这是什么

- 一套公开数据采集与交付 workflow；
- 有来源分级、证据链、质量校验和量化评估；
- 研究用户可以直接使用；
- 开发者可以通过 CLI / API / MCP 接入；
- examples 只是能力证明，而不是项目边界。

---

## 11. 风险与缓解

### 风险 1：只改文档，不补新样板，导致新叙事站不住

**缓解**：在完成叙事重构后，优先补 `global-public-stats`。

### 风险 2：过早大规模迁移目录，导致路径与文档断裂

**缓解**：采用分阶段迁移，先改叙事，后改结构。

### 风险 3：首页双入口写散，导致项目看起来像两个方向硬拼

**缓解**：坚持一个总主线：

> 公开数据采集与交付 workflow

研究用户与开发者只是这条 workflow 的两个使用视角。

---

## 12. 结论

本次重构的本质，不是给仓库换一套更时髦的说法，而是把项目从“若干 case 和工具脚本的集合”提升为“可复用、可接入、可证明边界更大的 workflow 框架”。

优先顺序必须明确：

1. 先改 README 和 docs，建立 workflow-first 身份；
2. 再把 `cases` 正式降级并迁移为 `examples`；
3. 再补全球公共统计与论文附录抽取样板，支撑新边界；
4. 最后再决定是否进行更大的命名与品牌调整。
