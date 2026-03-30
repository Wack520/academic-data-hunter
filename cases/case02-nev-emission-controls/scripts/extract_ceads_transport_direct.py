#!/usr/bin/env python3
"""
从 CEADs「30个省份排放清单」Excel 批量抽取交通运输部门直接排放（Scope_1_Total）。

输入目录默认：
cases/case02-nev-emission-controls/data/raw_ceads_sectoral_30prov/

输出文件默认：
cases/case02-nev-emission-controls/data/raw_ceads_sectoral_30prov/ceads_transport_co2_direct_30prov_2012_2022.csv
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
DEFAULT_INPUT_DIR = ROOT / "cases" / "case02-nev-emission-controls" / "data" / "raw_ceads_sectoral_30prov"
DEFAULT_OUTPUT = DEFAULT_INPUT_DIR / "ceads_transport_co2_direct_30prov_2012_2022.csv"

ENG2CN: dict[str, str] = {
    "Beijing": "北京市",
    "Tianjin": "天津市",
    "Hebei": "河北省",
    "Shanxi": "山西省",
    "InnerMongolia": "内蒙古自治区",
    "Liaoning": "辽宁省",
    "Jilin": "吉林省",
    "Heilongjiang": "黑龙江省",
    "Shanghai": "上海市",
    "Jiangsu": "江苏省",
    "Zhejiang": "浙江省",
    "Anhui": "安徽省",
    "Fujian": "福建省",
    "Jiangxi": "江西省",
    "Shandong": "山东省",
    "Henan": "河南省",
    "Hubei": "湖北省",
    "Hunan": "湖南省",
    "Guangdong": "广东省",
    "Guangxi": "广西壮族自治区",
    "Hainan": "海南省",
    "Chongqing": "重庆市",
    "Sichuan": "四川省",
    "Guizhou": "贵州省",
    "Yunnan": "云南省",
    "Shaanxi": "陕西省",
    "Gansu": "甘肃省",
    "Qinghai": "青海省",
    "Ningxia": "宁夏回族自治区",
    "Xinjiang": "新疆维吾尔自治区",
    "Tibet": "西藏自治区",
}


def extract_one_file(xlsx_path: Path) -> list[dict]:
    m_year = re.search(r"(20\d{2})", xlsx_path.name)
    if not m_year:
        return []
    year = int(m_year.group(1))

    rows: list[dict] = []
    xl = pd.ExcelFile(xlsx_path)
    for sheet in xl.sheet_names:
        if sheet.upper() == "NOTE":
            continue
        m_sheet = re.match(r"([A-Za-z]+)(20\d{2})$", sheet)
        if not m_sheet:
            continue
        prov_eng = m_sheet.group(1)
        province = ENG2CN.get(prov_eng)
        if not province:
            continue

        df = xl.parse(sheet)
        if df.empty:
            continue
        c0 = df.columns[0]
        s0 = df[c0].astype(str).str.strip()

        mask = s0.str.fullmatch(
            r"Transportation,\s*Storage,\s*Post\s*and\s*Telecommunication\s*Services",
            case=False,
            na=False,
        )
        if not mask.any():
            mask = s0.str.contains(r"Transportation,\s*Storage,\s*Post", case=False, regex=True, na=False)
        if not mask.any():
            mask = s0.str.contains(r"Transport", case=False, regex=True, na=False)

        if not mask.any():
            rows.append(
                {
                    "province": province,
                    "year": year,
                    "transport_co2_mt": None,
                    "source_file": xlsx_path.name,
                    "sheet": sheet,
                    "sector_label": "",
                }
            )
            continue

        r = df[mask].iloc[0]
        val_mt = pd.to_numeric(r.get("Scope_1_Total", None), errors="coerce")
        rows.append(
            {
                "province": province,
                "year": year,
                "transport_co2_mt": val_mt,
                "source_file": xlsx_path.name,
                "sheet": sheet,
                "sector_label": str(r.get(c0, "")),
            }
        )
    return rows


def main() -> None:
    in_dir = DEFAULT_INPUT_DIR
    files = sorted(in_dir.glob("*30个省份排放清单*.xlsx"))
    if not files:
        raise FileNotFoundError(f"未找到输入文件: {in_dir}")

    all_rows: list[dict] = []
    for f in files:
        all_rows.extend(extract_one_file(f))

    out = pd.DataFrame(all_rows).sort_values(["province", "year"]).reset_index(drop=True)
    out["transport_co2_10k_ton_direct"] = out["transport_co2_mt"] * 100
    out.to_csv(DEFAULT_OUTPUT, index=False, encoding="utf-8-sig")

    print(f"[OK] {DEFAULT_OUTPUT}")
    print(f"rows={len(out)}, non_na={out['transport_co2_mt'].notna().sum()}, provinces={out['province'].nunique()}")


if __name__ == "__main__":
    main()
