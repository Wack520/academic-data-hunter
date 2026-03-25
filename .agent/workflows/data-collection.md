---
description: 使用AI Agent搜集学术研究数据的标准工作流
---

# 数据搜集工作流

// turbo-all

## 1. 准备任务文档

复制模板并填写变量信息：

```bash
cp templates/task-spec-template.md my-task.md
```

编辑 `my-task.md`，替换所有 `{占位符}`：
- `{变量中文名}` → 如"公共充电桩"
- `{variable_name}` → 如"public_charging_piles"
- `{单位}` → 如"台"
- `{起始年份}` / `{结束年份}` → 如"2016" / "2023"

## 2. API/数据库优先搜集

如果变量可通过API获取：
```bash
python tools/stats_api_fetcher.py --indicator {指标ID} --years {范围}
```

如果需要下载数据库文件，手动下载后放到 `cases/caseXX/data/`。

## 3. 给 AI Agent（Codex）执行深度搜索

将任务文档内容发送给 Codex：
```
请阅读以下任务文档并按规范执行数据搜集：
[粘贴 my-task.md 内容]
```

## 4. 审查结果并补充

收到 Codex 结果后：
```bash
python tools/qc_checker.py data/output.csv --key province,year --required source_url
```

如有缺口，给 Codex 补充任务（使用 `templates/progress-report-template.md` 格式汇报进度）。

## 5. 合并到面板

```bash
python tools/panel_merger.py \
    --base data/panel.csv \
    --new data/output.csv \
    --on province,year \
    --map-province full
```

## 6. 最终QC

```bash
python tools/qc_checker.py data/panel.csv --key province,year
```

确认：
- 行数不变
- 新列非空数与源表一致
- 无重复键
