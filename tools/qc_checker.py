"""
QC Checker — 数据质量检查工具
用法: python qc_checker.py data.csv --key province,year --required source_url
"""
import argparse
import csv
import sys
from collections import Counter


def load_csv(path):
    with open(path, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def check_uniqueness(rows, key_cols):
    """检查主键唯一性"""
    keys = [tuple(r[k] for k in key_cols) for r in rows]
    dupes = {k: v for k, v in Counter(keys).items() if v > 1}
    return dupes


def check_required(rows, required_cols, value_col=None):
    """检查必填字段：当value_col有值时，required_cols不能为空"""
    issues = []
    for i, r in enumerate(rows):
        if value_col and not r.get(value_col, '').strip():
            continue  # 值为空时不检查来源
        for col in required_cols:
            if not r.get(col, '').strip():
                issues.append((i + 2, r.get('province', '?'), r.get('year', '?'), col))
    return issues


def print_coverage(rows, cols):
    """打印各列非空统计"""
    total = len(rows)
    print(f"\n{'列名':<40} {'非空':>6} / {total}  {'覆盖率':>8}")
    print('-' * 65)
    for col in cols:
        non_empty = sum(1 for r in rows if r.get(col, '').strip())
        pct = non_empty / total * 100 if total else 0
        print(f"{col:<40} {non_empty:>6} / {total}  {pct:>7.1f}%")


def main():
    parser = argparse.ArgumentParser(description='数据QC检查工具')
    parser.add_argument('csv_file', help='待检查的CSV文件')
    parser.add_argument('--key', default='province,year', help='主键列名(逗号分隔)')
    parser.add_argument('--required', default='source_url', help='必填列(逗号分隔)')
    parser.add_argument('--value-col', default=None, help='数值列(仅当此列有值时检查required)')
    args = parser.parse_args()

    rows = load_csv(args.csv_file)
    key_cols = [k.strip() for k in args.key.split(',')]
    required_cols = [k.strip() for k in args.required.split(',')]
    all_cols = list(rows[0].keys()) if rows else []

    print(f"📄 文件: {args.csv_file}")
    print(f"📊 总行数: {len(rows)}")
    print(f"📋 列数: {len(all_cols)}")

    # 1. 唯一性检查
    dupes = check_uniqueness(rows, key_cols)
    if dupes:
        print(f"\n❌ 主键重复 ({','.join(key_cols)}):")
        for k, v in dupes.items():
            print(f"   {k}: {v}次")
    else:
        print(f"\n✅ 主键唯一性: 通过 ({','.join(key_cols)})")

    # 2. 必填字段检查
    issues = check_required(rows, required_cols, args.value_col)
    if issues:
        print(f"\n❌ 必填字段缺失 ({','.join(required_cols)}):")
        for line, prov, year, col in issues[:10]:
            print(f"   行{line}: {prov} {year} 缺少 {col}")
        if len(issues) > 10:
            print(f"   ... 共{len(issues)}处")
    else:
        print(f"✅ 必填字段检查: 通过")

    # 3. 覆盖率统计
    print_coverage(rows, all_cols)

    # 返回码
    if dupes or issues:
        sys.exit(1)


if __name__ == '__main__':
    main()
