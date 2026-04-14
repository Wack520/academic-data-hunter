# Contributing Guide

感谢你参与 Academic Data Hunter！

## 1) 开发环境准备

```bash
python -m pip install -r requirements-lock.txt
python -m pip install -e ".[dev]"
pre-commit install
```

提交前建议本地执行：

```bash
python scripts/check_dependency_sync.py
python scripts/check_docs_command_paths.py
python scripts/run_review_gate.py
python scripts/summarize_workspace_changes.py
python -m ruff check .
python -m ruff format --check .
python -m mypy tools/ --ignore-missing-imports
python -m compileall -q scripts tools cases
python -m pytest -q tests/
```

依赖维护约定：

- 运行时依赖以 `pyproject.toml` 的 `[project].dependencies` 为主
- `requirements.txt` 与其保持一一同步（由 `scripts/check_dependency_sync.py` 守护）
- 发行锁定版本使用 `requirements-lock.txt`（Python 3.11）

## 2) 提交流程约定

1. 从 `main` 拉新分支（如 `feat/case04-population-density`）
2. 小步提交，commit message 尽量语义化（`refactor(...)` / `docs(...)` / `test(...)`）
3. 提交 PR 时说明：
   - 改动目标
   - 影响范围（scripts/tools/cases）
   - 如何验证（命令 + 结果）

---

## 3) 如何新增一个 Case

在 `cases/` 下建立目录：`caseXX-your-topic/`，建议结构：

```text
cases/caseXX-your-topic/
├─ data/
├─ scripts/
├─ progress-report.md
├─ search-log.md
└─ task-spec.md
```

建议流程：

1. 先写 `task-spec.md`，明确变量、单位、年份范围、可接受来源级别（A/B/C）
2. 在 `scripts/` 放 case 专属采集/处理脚本
3. 用 `scripts/run_round.py` 生成下一轮任务，用 `scripts/validate_round.py` + `tools/qc_checker.py` 做校验
4. 更新 `data/source_registry.csv`（如该 case 有来源台账）
5. 在 `progress-report.md` 记录覆盖率变化与未入库原因

---

## 4) 如何扩展搜索引擎（P10 架构）

搜索层位于 `tools/engines/`。

### 步骤 A：新增 Engine 类

1. 新建 `tools/engines/<engine_name>.py`
2. 继承 `SearchEngine` 并实现：

```python
def search(query: str, page, **kwargs) -> list[SearchResult]:
    ...
```

3. 返回统一 `SearchResult(title, url, snippet)`
4. 如需暴露反爬状态/统计信息，写入 `self.last_meta`

### 步骤 B：注册到 registry

在 `tools/engines/registry.py` 中加入映射：

```python
_ENGINE_REGISTRY["your_engine"] = YourEngine
```

### 步骤 C：联调 discover 编排层

`cases/case02-nev-emission-controls/scripts/discover_case02_nev_camoufox.py`
会通过 `get_engine(name)` 调度新引擎。

### 步骤 D：测试

- 至少补充 1 条单元/集成测试
- 运行 `pytest`、`ruff`、`mypy`

---

## 5) 行为边界

- 不直接修改 `cases/*/data/` 历史结果来“造通过”
- 不改变已有 CLI 参数语义（保持向后兼容）
- 所有自动化产出应可追溯（日志、报告、台账）
