"""
省份名称映射工具
支持：短名 ↔ 全名 ↔ 行政区划代码
"""

import logging
from typing import Literal, TypeAlias

ProvinceRecord: TypeAlias = dict[str, str]
ProvinceMap: TypeAlias = dict[str, ProvinceRecord]
ProvinceTarget: TypeAlias = Literal["short", "full", "code"]

# 30省映射表（剔除西藏及港澳台）
PROVINCE_MAP: ProvinceMap = {
    "北京": {"full": "北京市", "code": "110000"},
    "天津": {"full": "天津市", "code": "120000"},
    "河北": {"full": "河北省", "code": "130000"},
    "山西": {"full": "山西省", "code": "140000"},
    "内蒙古": {"full": "内蒙古自治区", "code": "150000"},
    "辽宁": {"full": "辽宁省", "code": "210000"},
    "吉林": {"full": "吉林省", "code": "220000"},
    "黑龙江": {"full": "黑龙江省", "code": "230000"},
    "上海": {"full": "上海市", "code": "310000"},
    "江苏": {"full": "江苏省", "code": "320000"},
    "浙江": {"full": "浙江省", "code": "330000"},
    "安徽": {"full": "安徽省", "code": "340000"},
    "福建": {"full": "福建省", "code": "350000"},
    "江西": {"full": "江西省", "code": "360000"},
    "山东": {"full": "山东省", "code": "370000"},
    "河南": {"full": "河南省", "code": "410000"},
    "湖北": {"full": "湖北省", "code": "420000"},
    "湖南": {"full": "湖南省", "code": "430000"},
    "广东": {"full": "广东省", "code": "440000"},
    "广西": {"full": "广西壮族自治区", "code": "450000"},
    "海南": {"full": "海南省", "code": "460000"},
    "重庆": {"full": "重庆市", "code": "500000"},
    "四川": {"full": "四川省", "code": "510000"},
    "贵州": {"full": "贵州省", "code": "520000"},
    "云南": {"full": "云南省", "code": "530000"},
    "陕西": {"full": "陕西省", "code": "610000"},
    "甘肃": {"full": "甘肃省", "code": "620000"},
    "青海": {"full": "青海省", "code": "630000"},
    "宁夏": {"full": "宁夏回族自治区", "code": "640000"},
    "新疆": {"full": "新疆维吾尔自治区", "code": "650000"},
}

# 反向映射
_FULL_TO_SHORT: dict[str, str] = {v["full"]: k for k, v in PROVINCE_MAP.items()}
_CODE_TO_SHORT: dict[str, str] = {v["code"]: k for k, v in PROVINCE_MAP.items()}


def short_to_full(name: str) -> str:
    """短名 → 全名：'北京' → '北京市'"""
    if name in PROVINCE_MAP:
        return PROVINCE_MAP[name]["full"]
    if name in _FULL_TO_SHORT:
        return name  # 已经是全名
    raise ValueError(f"未知省份: {name}")


def full_to_short(name: str) -> str:
    """全名 → 短名：'北京市' → '北京'"""
    if name in _FULL_TO_SHORT:
        return _FULL_TO_SHORT[name]
    if name in PROVINCE_MAP:
        return name  # 已经是短名
    raise ValueError(f"未知省份: {name}")


def normalize(name: str, target: ProvinceTarget = "short") -> str:
    """
    省份名标准化
    target: 'short' | 'full' | 'code'
    """
    # 先统一为短名
    short = name
    if name in _FULL_TO_SHORT:
        short = _FULL_TO_SHORT[name]
    elif name in _CODE_TO_SHORT:
        short = _CODE_TO_SHORT[name]
    elif name not in PROVINCE_MAP:
        # 尝试模糊匹配（去掉"省/市/自治区"后缀）
        for s in PROVINCE_MAP:
            if name.startswith(s):
                short = s
                break
        else:
            raise ValueError(f"未知省份: {name}")

    if target == "short":
        return short
    if target == "full":
        return PROVINCE_MAP[short]["full"]
    if target == "code":
        return PROVINCE_MAP[short]["code"]
    raise ValueError(f"target必须为 short/full/code, 收到: {target}")


def get_all_provinces(target: ProvinceTarget = "short") -> list[str]:
    """返回30省列表"""
    if target == "short":
        return list(PROVINCE_MAP.keys())
    if target == "full":
        return [v["full"] for v in PROVINCE_MAP.values()]
    if target == "code":
        return [v["code"] for v in PROVINCE_MAP.values()]
    raise ValueError(f"target必须为 short/full/code, 收到: {target}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    logging.info("30省短名: %s", get_all_provinces("short"))
    logging.info("映射测试:")
    for name in ["北京", "北京市", "内蒙古自治区", "广西壮族自治区"]:
        logging.info("  %s → short=%s, full=%s", name, normalize(name, "short"), normalize(name, "full"))
