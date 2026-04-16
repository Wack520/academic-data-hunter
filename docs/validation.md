# 校验说明

交付前至少要做以下检查。

## 行级检查

- 必填字段存在
- 主键不重复
- 数值字段可解析
- 单位与口径一致
- 来源字段完整

## 表级检查

- 数据表与来源台账能匹配
- evidence 记录与数据表能对应
- 覆盖率变化可解释

## 当前仓库中的常用检查

- `python scripts/validate_round.py`
- `python scripts/check_docs_command_paths.py --paths README.md CONTRIBUTING.md docs .github`
- `python -m pytest -q`
