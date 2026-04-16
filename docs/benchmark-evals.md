# Benchmark Eval 评估

Benchmark Eval 用来回答一个直接问题：

> 这次数据交付，质量到底怎么样？

## 当前评估指标

- **fill rate**：目标面板填充率
- **provenance completeness**：来源信息完整度
- **registry match rate**：数据表与来源台账匹配率
- **C-level cross-check rate**：C 级来源交叉核验率
- **source quality score**：来源质量分

这些指标会汇总成一个 **overall score（0-100）**。

## 为什么需要它

研究型数据工作不只关心“找到了多少”，还关心：

- 缺口还有多少
- 来源是否完整
- 台账是否对得上
- 当前结果是否足够进入建模或写作

## 运行命令

```bash
python scripts/run_benchmark_eval.py ^
  --data cases/case01-nev-carbon/data/charging_piles_by_province.csv ^
  --registry cases/case01-nev-carbon/data/source_registry.csv ^
  --variable charging ^
  --value-col public_charging_piles ^
  --year-start 2017 ^
  --year-end 2023 ^
  --output-json tmp/benchmark/case01-charging.json ^
  --output-md tmp/benchmark/case01-charging.md
```

## 输出文件

- `*.json`：给脚本或系统继续处理
- `*.md`：给人直接查看

## 当前特点

第一版评分模型故意保持简单、稳定、可解释，方便先把“研究数据交付是否可靠”量化出来。
