#!/usr/bin/env python3
"""
Case02 自动采集脚本：
- 从国家统计局 data.stats.gov.cn 抓取 30省 2012-2023 控制变量
- 合并本地 NEV 保有量
- 基于油耗估算交通碳排放
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
import textwrap
import urllib.parse
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import requests

from tools.province_mapper import get_all_provinces, normalize

ROOT = Path(__file__).resolve().parents[3]

BASE_URL = "https://data.stats.gov.cn"
CASE_DIR = ROOT / "cases" / "case02-nev-emission-controls"
DATA_DIR = CASE_DIR / "data"


TARGET_YEARS = list(range(2012, 2024))
TARGET_PROVINCES = get_all_provinces("full")


NBS_SPECS = [
    ("gdp_100m_cny", "A020101", "地区生产总值"),
    ("tertiary_value_added_100m_cny", "A020104", "第三产业增加值"),
    ("resident_population_10k_person", "A030101", "年末常住人口"),
    ("urban_population_10k_person", "A030102", "城镇人口"),
    ("passenger_turnover_100m_pkm", "A0G0401", "旅客周转量"),
    ("freight_turnover_100m_tkm", "A0G0601", "货物周转量"),
    ("road_mileage_10k_km", "A0G0203", "公路里程"),
]


@dataclass
class NBSMeta:
    code: str
    name: str
    unit: str
    source_url: str


def _solve_challenge_js(js_text: str) -> tuple[str, str]:
    """执行反爬JS，得到下一跳URL与cookie。"""
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        js_file = td / "challenge.js"
        run_file = td / "run.js"
        js_file.write_text(js_text, encoding="utf-8")
        run_file.write_text(
            textwrap.dedent(
                f"""
                const fs=require('fs');
                const {{TextDecoder}}=require('util');
                global.TextDecoder=TextDecoder;
                let lastLocation='';
                const locationObj={{hostname:'data.stats.gov.cn',protocol:'https:',href:'https://data.stats.gov.cn/'}};
                const windowObj={{}};
                Object.defineProperty(windowObj,'location',{{
                  get(){{return locationObj;}},
                  set(v){{lastLocation=v; locationObj.href=v;}}
                }});
                global.window=windowObj;
                const doc={{
                  createElement:(tag)=>({{tagName:tag,style:{{}},appendChild:()=>{{}},submit:()=>{{}},setAttribute:()=>{{}}}}),
                  body:{{appendChild:()=>{{}}}},
                  cookie:''
                }};
                global.document=doc;
                global.setInterval=(fn,ms)=>0;
                global.clearInterval=(id)=>{{}};
                try {{
                  const code = fs.readFileSync({str(js_file)!r}, 'utf8');
                  eval(code);
                  console.log(JSON.stringify({{location:lastLocation,cookie:doc.cookie||''}}));
                }} catch(e) {{
                  console.log(JSON.stringify({{error:String(e&&e.stack?e.stack:e),location:lastLocation,cookie:doc.cookie||''}}));
                }}
                """
            ),
            encoding="utf-8",
        )
        proc = subprocess.run(
            ["node", str(run_file)],
            capture_output=True,
            text=True,
            timeout=25,
        )
        out = proc.stdout.strip().splitlines()
        if not out:
            raise RuntimeError(f"challenge js执行失败: {proc.stderr[:200]}")
        obj = json.loads(out[-1])
        if obj.get("error"):
            raise RuntimeError(f"challenge js错误: {obj['error'][:200]}")
        return obj.get("location", ""), obj.get("cookie", "")


def _apply_cookie_string(session: requests.Session, cookie_str: str) -> None:
    if not cookie_str:
        return
    for part in cookie_str.split(";"):
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        lk = k.strip().lower()
        if lk in {"path", "domain", "expires", "max-age", "secure", "httponly", "samesite"}:
            continue
        session.cookies.set(k.strip(), v.strip(), domain="data.stats.gov.cn")


def _request_with_challenge(session: requests.Session, url: str, max_rounds: int = 8) -> requests.Response:
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://data.stats.gov.cn/easyquery.htm?cn=E0103",
    }
    current = url
    for _ in range(max_rounds):
        resp = session.get(current, headers=headers, timeout=30)
        txt = resp.text.lstrip()
        if txt.startswith("{") or txt.startswith("["):
            return resp
        m = re.search(r"<script type=\"text/javascript\">(.*?)</script>", resp.text, re.S)
        if not m:
            raise RuntimeError(f"未找到challenge脚本: {resp.text[:120]}")
        nxt, cookie = _solve_challenge_js(m.group(1))
        _apply_cookie_string(session, cookie)
        if not nxt:
            raise RuntimeError("challenge返回空跳转")
        current = urllib.parse.urljoin(BASE_URL, nxt)
    raise RuntimeError("challenge轮次超限")


def fetch_nbs_variable(session: requests.Session, code: str, value_col: str) -> tuple[pd.DataFrame, NBSMeta]:
    params = {
        "m": "QueryData",
        "dbcode": "fsnd",
        "rowcode": "reg",
        "colcode": "sj",
        "wds": json.dumps([{"wdcode": "zb", "valuecode": code}], ensure_ascii=False),
        "dfwds": json.dumps([{"wdcode": "sj", "valuecode": "2012-2023"}], ensure_ascii=False),
    }
    query_url = BASE_URL + "/easyquery.htm?" + urllib.parse.urlencode(params)
    resp = _request_with_challenge(session, query_url)
    payload = resp.json()
    rd = payload.get("returndata", {})

    wdnodes = rd.get("wdnodes", [])
    zb_nodes = next((x.get("nodes", []) for x in wdnodes if x.get("wdcode") == "zb"), [])
    reg_nodes = next((x.get("nodes", []) for x in wdnodes if x.get("wdcode") == "reg"), [])

    if not zb_nodes:
        raise RuntimeError(f"{code} 无zb节点")
    zb = zb_nodes[0]
    meta = NBSMeta(
        code=zb.get("code", code),
        name=zb.get("cname", zb.get("name", code)),
        unit=zb.get("unit", ""),
        source_url=query_url,
    )

    reg_map = {x.get("code"): x.get("cname", x.get("name", "")) for x in reg_nodes}
    rows: list[dict] = []
    for dn in rd.get("datanodes", []):
        wds = {w.get("wdcode"): w.get("valuecode") for w in dn.get("wds", [])}
        reg = wds.get("reg")
        sj = wds.get("sj")
        if reg not in reg_map:
            continue
        try:
            year = int(sj)
        except Exception:
            continue
        if year not in TARGET_YEARS:
            continue
        province = reg_map[reg]
        if province not in TARGET_PROVINCES:
            continue
        data_obj = dn.get("data", {}) or {}
        val = data_obj.get("data") if data_obj.get("hasdata", False) else None
        rows.append({"province": province, "year": year, value_col: val})

    df = pd.DataFrame(rows).drop_duplicates(subset=["province", "year"], keep="last")
    return df, meta


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 1) 拉取NBS变量
    session = requests.Session()
    nbs_metas: dict[str, NBSMeta] = {}
    nbs_frames: list[pd.DataFrame] = []

    for value_col, code, _label in NBS_SPECS:
        print(f"[NBS] fetching {value_col} <- {code}")
        df, meta = fetch_nbs_variable(session, code, value_col)
        nbs_metas[value_col] = meta
        nbs_frames.append(df)
        out = DATA_DIR / f"nbs_{value_col}.csv"
        df.sort_values(["province", "year"]).to_csv(out, index=False, encoding="utf-8-sig")
        print(f"  saved: {out} rows={len(df)}")

    # 2) 面板骨架
    panel = pd.MultiIndex.from_product(
        [TARGET_PROVINCES, TARGET_YEARS],
        names=["province", "year"],
    ).to_frame(index=False)

    for df in nbs_frames:
        panel = panel.merge(df, on=["province", "year"], how="left")

    # 3) 衍生控制变量
    panel["gdp_per_capita_yuan"] = panel["gdp_100m_cny"] * 10000 / panel["resident_population_10k_person"]
    panel["urbanization_rate"] = panel["urban_population_10k_person"] / panel["resident_population_10k_person"]
    panel["tertiary_share"] = panel["tertiary_value_added_100m_cny"] / panel["gdp_100m_cny"]

    # 4) 合并 NEV 保有量（本地已有结果）
    nev_path = ROOT.parent / "math" / "data_collector" / "output" / "nev_stock_30prov_2012_2023.csv"
    if not nev_path.exists():
        raise FileNotFoundError(f"缺少NEV文件: {nev_path}")
    nev_df = pd.read_csv(nev_path)
    nev_df["province"] = nev_df["province"].map(lambda x: normalize(str(x), "full"))
    nev_df = nev_df.rename(columns={"nev_stock_10k": "nev_stock_10k"})[["province", "year", "nev_stock_10k"]]
    panel = panel.merge(nev_df, on=["province", "year"], how="left")

    # 5) 估算交通碳排放（优先使用含filled油耗的合并面板）
    case01_panel = ROOT / "cases" / "case01-nev-carbon" / "data" / "panel_30prov_2012_2023.csv"
    merged_panel_with_filled = (
        ROOT.parent / "math" / "merged_output" / "all_priorities_merged_panel_30prov_2012_2023.csv"
    )
    fuel_source = merged_panel_with_filled if merged_panel_with_filled.exists() else case01_panel
    if not fuel_source.exists():
        raise FileNotFoundError(f"缺少油耗来源面板: {fuel_source}")

    fuel_raw = pd.read_csv(fuel_source)
    req_cols = ["province", "year", "gasoline_consumption_10k_ton", "diesel_consumption_10k_ton"]
    for c in req_cols:
        if c not in fuel_raw.columns:
            raise KeyError(f"{fuel_source} 缺少字段: {c}")
    fuel_df = fuel_raw[req_cols].copy()
    if "gasoline_consumption_10k_ton_filled" in fuel_raw.columns:
        fuel_df["gasoline_consumption_10k_ton"] = fuel_df["gasoline_consumption_10k_ton"].where(
            fuel_df["gasoline_consumption_10k_ton"].notna(),
            fuel_raw["gasoline_consumption_10k_ton_filled"],
        )
    if "diesel_consumption_10k_ton_filled" in fuel_raw.columns:
        fuel_df["diesel_consumption_10k_ton"] = fuel_df["diesel_consumption_10k_ton"].where(
            fuel_df["diesel_consumption_10k_ton"].notna(),
            fuel_raw["diesel_consumption_10k_ton_filled"],
        )
    # 系数近似：汽油2.925、柴油3.096 tCO2 / t燃料
    fuel_df["transport_co2_est_10k_ton"] = (
        fuel_df["gasoline_consumption_10k_ton"] * 2.925 + fuel_df["diesel_consumption_10k_ton"] * 3.096
    )
    panel = panel.merge(
        fuel_df[["province", "year", "transport_co2_est_10k_ton"]],
        on=["province", "year"],
        how="left",
    )

    # 6) 输出
    keep_cols = [
        "province",
        "year",
        "transport_co2_est_10k_ton",
        "nev_stock_10k",
        "gdp_per_capita_yuan",
        "urbanization_rate",
        "passenger_turnover_100m_pkm",
        "freight_turnover_100m_tkm",
        "road_mileage_10k_km",
        "tertiary_share",
        # 附带原始列，便于复核
        "gdp_100m_cny",
        "tertiary_value_added_100m_cny",
        "resident_population_10k_person",
        "urban_population_10k_person",
    ]
    panel = panel[keep_cols].sort_values(["province", "year"]).reset_index(drop=True)
    out_panel = DATA_DIR / "panel_case02_30prov_2012_2023.csv"
    panel.to_csv(out_panel, index=False, encoding="utf-8-sig")
    print(f"[OK] saved panel: {out_panel} rows={len(panel)}")

    # 7) source registry
    access_date = pd.Timestamp.now().strftime("%Y-%m-%d")
    registry_rows = []
    for idx, (value_col, _code, _label) in enumerate(NBS_SPECS, start=1):
        m = nbs_metas[value_col]
        registry_rows.append(
            {
                "source_id": f"SRC_CASE02_NBS_{idx:02d}",
                "variable": value_col,
                "source_level": "A",
                "source_name": f"国家统计局-国家数据({m.name})",
                "source_url": "https://data.stats.gov.cn/easyquery.htm?cn=E0103",
                "cross_check_url": "",
                "publish_date": "",
                "access_date": access_date,
                "evidence_file": f"nbs_{value_col}.csv",
                "is_primary": 1,
                "note": f"指标代码={m.code}; 单位={m.unit}",
            }
        )

    nev_source_url = nev_path.resolve().as_uri()
    fuel_source_url = fuel_source.resolve().as_uri()

    registry_rows.append(
        {
            "source_id": "SRC_CASE02_NEV_01",
            "variable": "nev_stock_10k",
            "source_level": "B",
            "source_name": "本地NEV保有量数据（math/data_collector）",
            "source_url": nev_source_url,
            "cross_check_url": "",
            "publish_date": "",
            "access_date": access_date,
            "evidence_file": str(nev_path.relative_to(ROOT.parent)),
            "is_primary": 0,
            "note": "由历史采集流程生成，作为NEV变量输入",
        }
    )
    registry_rows.append(
        {
            "source_id": "SRC_CASE02_CO2_EST_01",
            "variable": "transport_co2_est_10k_ton",
            "source_level": "B",
            "source_name": "基于case01油耗数据的交通碳排放估算",
            "source_url": fuel_source_url,
            "cross_check_url": "",
            "publish_date": "",
            "access_date": access_date,
            "evidence_file": str(fuel_source.relative_to(ROOT.parent)),
            "is_primary": 0,
            "note": "估算公式: 汽油*2.925 + 柴油*3.096 (tCO2/t燃料), 输出单位=万吨CO2；原值缺失时优先使用*_filled；系数说明参见 IPCC 2006 Guidelines Vol.2, Table 3.2.1（论文中需明确口径）",
        }
    )
    reg_df = pd.DataFrame(registry_rows)
    reg_out = DATA_DIR / "source_registry.csv"
    reg_df.to_csv(reg_out, index=False, encoding="utf-8-sig")
    print(f"[OK] saved registry: {reg_out} rows={len(reg_df)}")

    # 8) case README
    readme = CASE_DIR / "README.md"
    readme.write_text(
        textwrap.dedent(
            f"""\
            # case02-nev-emission-controls

            本案例输出 30省 × 2012-2023 的控制变量面板，目标变量如下：
            - `transport_co2_est_10k_ton`（交通碳排放估算）
            - `nev_stock_10k`（新能源汽车保有量）
            - `gdp_per_capita_yuan`（人均GDP）
            - `urbanization_rate`（城镇化率）
            - `passenger_turnover_100m_pkm`（客运周转量）
            - `freight_turnover_100m_tkm`（货运周转量）
            - `road_mileage_10k_km`（公路里程）
            - `tertiary_share`（第三产业占比）

            ## 文件说明
            - `task-spec.md`：任务规格
            - `progress-report.md`：执行进展与覆盖率
            - `search-log.md`：搜索/采集日志
            - `comparison_with_delivery.md`：与 `math/交付数据_30省面板_2012_2023` 对比报告
            - `next-round-task.md`：自动补缺任务单（本轮已无缺口）
            - `auto-round-report.md`：自动多轮调度报告
            - `data/panel_case02_30prov_2012_2023.csv`：最终面板
            - `data/source_registry.csv`：来源台账
            - `data/nbs_*.csv`：分指标原始抓取文件

            ## 复现命令
            ```bash
            python cases/case02-nev-emission-controls/scripts/collect_case02.py
            python cases/case02-nev-emission-controls/scripts/export_case02_xlsx.py
            python cases/case02-nev-emission-controls/scripts/qc_case02.py
            python cases/case02-nev-emission-controls/scripts/compare_case02_with_delivery.py
            python scripts/run_round.py --data cases/case02-nev-emission-controls/data/panel_case02_30prov_2012_2023.csv --value-col transport_co2_est_10k_ton --keyword-name 交通碳排放估算 --keyword-template1 "{{省名}} {{keyword_name}} {{year}}" --keyword-template2 "{{省名}} 交通运输 二氧化碳排放 {{year}}" --year-start 2012 --year-end 2023 --top-years 2 --output cases/case02-nev-emission-controls/next-round-task.md
            python scripts/run_auto_rounds.py --data cases/case02-nev-emission-controls/data/panel_case02_30prov_2012_2023.csv --value-col transport_co2_est_10k_ton --year-start 2012 --year-end 2023 --max-rounds 2 --task-output cases/case02-nev-emission-controls/next-round-task.md --report cases/case02-nev-emission-controls/auto-round-report.md
            ```

            ## 说明
            - NBS 指标由脚本自动采集（含 challenge 处理）。
            - 交通碳排放为基于油耗的估算值（非官方直接发布“交通碳排放”统计口径）。
            - 生成时间：{pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")}
            """
        ),
        encoding="utf-8",
    )
    print(f"[OK] wrote {readme}")

    # 9) 简要覆盖率
    for c in [
        "transport_co2_est_10k_ton",
        "nev_stock_10k",
        "gdp_per_capita_yuan",
        "urbanization_rate",
        "passenger_turnover_100m_pkm",
        "freight_turnover_100m_tkm",
        "road_mileage_10k_km",
        "tertiary_share",
    ]:
        non_na = panel[c].notna().sum()
        print(f"[COVERAGE] {c}: {non_na}/{len(panel)}")


if __name__ == "__main__":
    main()
