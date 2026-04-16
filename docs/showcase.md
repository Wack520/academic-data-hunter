# 项目展示

这份文档用来快速说明：这个项目现在已经能交付什么。

## 1. 已有真实案例

仓库里不是空模板，而是已经放了可直接查看的真实案例：

- `case01-nev-carbon`
- `case02-nev-emission-controls`
- `case03-population-10y`

## 2. 已能导出完整交付包

一次任务的结果不只是一张表，还可以导出：

```text
task spec
  -> next-round task
  -> dataset.csv
  -> source_registry.csv
  -> evidence_records.jsonl
  -> benchmark report
```

## 3. 已能量化评估结果

来自 `case01-nev-carbon` 的一次真实评估结果：

| 指标 | 数值 |
|---|---:|
| 填充率 | 40.95 |
| 来源完整性 | 100.00 |
| 台账匹配率 | 100.00 |
| C级来源交叉核验率 | 100.00 |
| 来源质量分 | 59.53 |
| 总分 | 73.26 |

## 4. 已有可接入的工具入口

当前可用入口：

- CLI 脚本
- Agent Hub API
- 本地 stdio MCP Server

## 5. 项目当前最有价值的地方

它把研究型数据工作里最容易被忽略的一层做成了可复用工具：

- 数据采集
- 来源登记
- 质量校验
- 交付包导出
- 量化评估
