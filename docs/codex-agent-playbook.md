# Codex Agent 适配手册（回合制）

## 目标

将“搜索能力”与“审计能力”解耦：

- 搜索执行：由 Codex / 其他 Agent 执行
- 审计入库：由本仓库模板 + QC 工具约束

## 标准回合

1. 生成下一轮任务
2. 让 Agent 按任务搜集
3. 校验与回写
4. 进入下一轮

## 1) 生成下一轮任务

```bash
python scripts/run_round.py \
  --data cases/case01-nev-carbon/data/charging_piles_by_province.csv \
  --value-col public_charging_piles \
  --keyword-name 公共充电桩 \
  --keyword-template1 "{省名} {keyword_name} {year} 保有量 台" \
  --keyword-template2 "{省名} {keyword_name} {year} 截至 台" \
  --year-start 2017 \
  --year-end 2023 \
  --top-years 2 \
  --output cases/case01-nev-carbon/next-round-task.md
```

## 2) 发给 Agent 的最小指令

```text
请阅读 cases/case01-nev-carbon/next-round-task.md 并执行。
要求：
1) 仅补缺失省份；禁止覆盖已有值
2) 每条新增值必须有 source_url/source_name/source_level
3) C级来源必须给 cross_check_url（至少1条）
4) 搜不到就留空，并在 progress-report 记录未入库原因
```

## 3) 回仓库验证

```bash
python scripts/validate_round.py \
  --data cases/case01-nev-carbon/data/charging_piles_by_province.csv \
  --registry cases/case01-nev-carbon/data/source_registry.csv \
  --variable charging \
  --value-col public_charging_piles \
  --check-unit 台
# 需要严格模式时追加:
# --strict-c-cross-check
```

Case01 全量校验可直接运行：

```bash
python cases/case01-nev-carbon/scripts/qc_case01.py
```

## 自动多轮模式（接入任意Agent）

```bash
python scripts/run_auto_rounds.py \
  --data cases/case01-nev-carbon/data/charging_piles_by_province.csv \
  --value-col public_charging_piles \
  --year-start 2017 \
  --year-end 2023 \
  --agent-cmd "your_agent_runner --task {task_file}" \
  --validate-cmd "python scripts/validate_round.py --data {data} --registry cases/case01-nev-carbon/data/source_registry.csv --variable charging --value-col public_charging_piles --check-unit 台 --strict-c-cross-check"
```

命令模板占位符：
- `{task_file}`：本轮任务文档路径
- `{round}`：轮次（从1开始）
- `{data}`：目标CSV路径
- `{repo_root}`：仓库根目录

## Hybrid Agent 入口

```bash
# API
python scripts/agent_hub.py serve --host 127.0.0.1 --port 8787

# 交互式
python scripts/agent_hub.py chat
```

## 4) 常用红线

- 禁止估算/推算/插值/外推
- 禁止无 URL 入库
- 口径不一致宁可留空
- 同省同年冲突时优先级：A > B > C
