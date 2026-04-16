# Academic Data Hunter 架构说明

本文档描述项目核心模块、数据流与扩展点，便于后续维护和开源协作。

## 1. 端到端数据流

```mermaid
flowchart TD
    A[任务输入<br/>task-spec / research-spec] --> B[plan_research_workflow.py]
    B --> C[run_round.py<br/>生成下一轮任务]
    C --> D[Agent 执行层<br/>执行型 Agent / MCP 客户端]
    D --> E[Case 数据文件更新<br/>cases/*/data/*.csv]
    E --> F[validate_round.py]
    F --> G[qc_checker.py]
    G --> H[panel_merger.py]
    H --> I[进度报告 / source_registry]
    I --> K[export_evidence_pack.py<br/>Evidence Pack Bundle]
    I --> J[run_auto_rounds.py<br/>增益评估与早停]
    J --> C
```

## 2. 搜索引擎抽象层（Case02）

```mermaid
flowchart LR
    A[discover_case02_nev_camoufox.py<br/>薄编排层] --> B[tools.engines.registry.get_engine]
    B --> C1[GoogleEngine]
    B --> C2[BingEngine]
    B --> C3[SogouEngine]
    B --> C4[So360Engine]
    B --> C5[TavilyEngine]

    A --> D[tools.fetcher<br/>fetch_text + cache]
    A --> E[tools.candidate_extractor<br/>extract / score / dedup]
    E --> F[候选结果 JSON]
```

## 3. 模块依赖关系

```mermaid
flowchart TD
    subgraph CoreTools[tools/]
        PM[province_mapper.py]
        QC[qc_checker.py]
        MG[panel_merger.py]
        MD[models.py]
        FE[fetcher.py]
        CE[candidate_extractor.py]
        EN[engines/*]
    end

    RR[scripts/run_round.py] --> PM
    AR[scripts/run_auto_rounds.py] --> PM
    VR[scripts/validate_round.py] --> QC
    VR --> MD
    AH[scripts/agent_hub.py] --> RR
    AH --> AR
    AH --> VR
    AH --> EP[export_evidence_pack.py]

    D2[cases/case02.../discover_case02_nev_camoufox.py] --> EN
    D2 --> FE
    D2 --> CE
    QC --> MD
    MG --> PM
```

## 4. 设计原则

1. **脚本编排、工具纯逻辑分离**：`scripts/` 负责流程，`tools/` 负责可复用能力。  
2. **Case 代码就近管理**：案例专属脚本放在 `cases/<case>/scripts/`。  
3. **输入先校验再处理**：使用 Pydantic 模型约束关键字段。  
4. **可审计优先**：每次自动化轮次都要可追溯（任务文件、报告、台账）。  
5. **可扩展搜索层**：新增搜索引擎只需实现 `SearchEngine` 并注册到 `registry`。  
6. **交付物优先**：最终输出不止是 CSV，还应包含 `source_registry` 与 `evidence pack`。  

## 5. 运行模式

- **本地脚本模式**：直接调用 `python scripts/*.py`
- **Hub API 模式**：`python scripts/agent_hub.py serve ...`
- **容器模式**：见仓库根目录 `Dockerfile` 和 `docker-compose.yml`
- **Evidence Pack 模式**：`python scripts/export_evidence_pack.py ...`
