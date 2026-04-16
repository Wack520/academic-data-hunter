# Evidence Pack 交付包

Evidence Pack 是这个项目的核心交付物。

它解决的不是“有没有找到数据”，而是“这份数据能不能交给别人继续分析和复核”。

## 为什么不只给 CSV

只交一份 CSV，通常还缺这些信息：

- 数据值来自哪里
- 来源属于什么等级
- 是否做过交叉核验
- 数据表与来源台账能否对上

Evidence Pack 就是把这些一起交出去。

## 当前输出结构

```text
output/
  manifest.json
  dataset.csv
  source_registry.csv
  evidence_records.jsonl
  README.md
```

## 导出命令

```bash
python scripts/export_evidence_pack.py ^
  --data cases/case01-nev-carbon/data/charging_piles_by_province.csv ^
  --registry cases/case01-nev-carbon/data/source_registry.csv ^
  --variable charging ^
  --value-col public_charging_piles ^
  --output-dir tmp/evidence-pack/case01-charging
```

## evidence_records.jsonl 里有什么

每条记录会保留：

- 对应的数据行键值
- 选中的数值字段
- 行级来源信息
- 匹配到的来源台账记录
- 匹配方式（`source_id` / `source_tuple` / `unmatched`）

## 适合什么场景

- 研究助理向老师交数据
- 建模比赛队内交接数据
- 论文附录前的复核
- Agent 输出转成可审计交付物
