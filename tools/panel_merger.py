"""
面板数据合并工具
用法: python panel_merger.py --base panel.csv --new data.csv --on province,year --map-province short-to-full
"""
import argparse
import csv
import sys

try:
    from province_mapper import normalize
except ImportError:
    sys.path.insert(0, '.')
    from province_mapper import normalize


def load_csv(path):
    with open(path, encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))


def save_csv(rows, path, fieldnames):
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def merge_panel(base_rows, new_rows, key_cols, new_cols, province_target=None):
    """左连接合并"""
    # 建立新数据索引
    new_index = {}
    for r in new_rows:
        prov = r.get('province', '')
        if province_target:
            try:
                prov = normalize(prov, province_target)
            except ValueError:
                pass
        key = tuple([prov if k == 'province' else r.get(k, '') for k in key_cols])
        new_index[key] = r

    # 合并
    merged = 0
    for r in base_rows:
        key = tuple(r.get(k, '') for k in key_cols)
        match = new_index.get(key)
        if match:
            for col in new_cols:
                if col in match and match[col].strip():
                    r[col] = match[col]
                    merged += 1

    return base_rows, merged


def main():
    parser = argparse.ArgumentParser(description='面板数据合并工具')
    parser.add_argument('--base', required=True, help='基础面板CSV')
    parser.add_argument('--new', required=True, help='新数据CSV')
    parser.add_argument('--on', default='province,year', help='连接键')
    parser.add_argument('--cols', default=None, help='要合并的列(逗号分隔,默认取new中非键列)')
    parser.add_argument('--map-province', default=None, 
                        choices=['short', 'full'], help='省份名映射目标格式')
    parser.add_argument('--output', default=None, help='输出文件(默认覆盖base)')
    args = parser.parse_args()

    base = load_csv(args.base)
    new = load_csv(args.new)
    key_cols = [k.strip() for k in args.on.split(',')]

    if args.cols:
        new_cols = [k.strip() for k in args.cols.split(',')]
    else:
        new_cols = [k for k in new[0].keys() if k not in key_cols]

    print(f"📊 基础面板: {len(base)} 行")
    print(f"📄 新数据: {len(new)} 行, 合并列: {new_cols}")

    # 为base添加新列（如不存在）
    for col in new_cols:
        for r in base:
            if col not in r:
                r[col] = ''

    base, merged = merge_panel(base, new, key_cols, new_cols, args.map_province)

    fieldnames = list(base[0].keys())
    output = args.output or args.base
    save_csv(base, output, fieldnames)

    print(f"✅ 合并完成: {merged} 个值已填入")
    print(f"💾 输出: {output}")

    # 统计
    for col in new_cols:
        non_empty = sum(1 for r in base if r.get(col, '').strip())
        print(f"   {col}: {non_empty}/{len(base)} 非空")


if __name__ == '__main__':
    main()
