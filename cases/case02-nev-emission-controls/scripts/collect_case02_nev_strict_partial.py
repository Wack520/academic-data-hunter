#!/usr/bin/env python3
"""
严格口径（官方原文）补采：NEV 保有量（当前轮次：部分省份）

策略：
- 仅接收官方网页中可直接定位的“保有量”表述；
- 仅写入明确年份（当前写入 2023 年）；
- 不插值、不外推。
"""

from __future__ import annotations

import csv
import re
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import requests
import urllib3
from bs4 import BeautifulSoup
from requests.exceptions import SSLError

ROOT = Path(__file__).resolve().parents[3]
CASE_DIR = ROOT / "cases" / "case02-nev-emission-controls"
DATA_DIR = CASE_DIR / "data"
PANEL_PATH = DATA_DIR / "panel_case02_strict_30prov_2012_2023.csv"
REG_PATH = DATA_DIR / "source_registry_strict.csv"
NEV_OUT = DATA_DIR / "nev_stock_strict_2023_partial.csv"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


@dataclass
class NevSource:
    province: str
    year: int
    source_id: str
    source_name: str
    source_url: str
    publish_date: str
    regex: str
    note: str
    scale_to_10k: float = 1.0
    backup_urls: list[str] | None = None


SOURCES: list[NevSource] = [
    NevSource(
        province="北京市",
        year=2023,
        source_id="SRC_CASE02_STRICT_NEV_2023_BJ",
        source_name="北京市发展改革委-北京加快布局新能源汽车超级充电站",
        source_url="https://fgw.beijing.gov.cn/gzdt/fgzs/mtbdx/bzwlxw/202408/t20240820_3777559.htm",
        publish_date="2024-08-20",
        regex=r"2023年[^。]{0,120}?北京(?:市)?全市新能源汽车保有量(?:达到|达|为|超)([0-9]+(?:\.[0-9]+)?)万辆",
        note="原文明确“2023年，北京全市新能源汽车保有量达到77.3万辆”。",
    ),
    NevSource(
        province="甘肃省",
        year=2023,
        source_id="SRC_CASE02_STRICT_NEV_2023_GS",
        source_name="景泰县人民政府-关于向社会发布全省机动车和驾驶人保有量等基本数据的公示",
        source_url="https://www.jingtai.gov.cn/zfxxgk/bmhxzxxgk/xzfzcbmzsjgml/xgaj/fdzdgknr/gsgg/art/2024/art_85e3c3c630264fbd9821d09e2249a038.html",
        publish_date="2024-02-28",
        regex=r"全省新能源(?:汽车|车)保有量([0-9]+(?:\.[0-9]+)?)辆",
        note="县级政府站转载省公安交管局公示原文；值为“辆”，已换算为“万辆”（÷10000）。",
        scale_to_10k=0.0001,
    ),
    NevSource(
        province="贵州省",
        year=2023,
        source_id="SRC_CASE02_STRICT_NEV_2023_GZ",
        source_name="贵州省发改委-2023年贵州省经济运行稳中向好",
        source_url="https://drc.guizhou.gov.cn/xwzx/zwyw/202401/t20240112_83529665.html",
        publish_date="2024-01-12",
        regex=r"截至2023年12月22日[^。]{0,140}?(?:全省|贵州省)新能源汽车保有量(?:达到|达|为|超)([0-9]+(?:\.[0-9]+)?)万辆",
        note="原文为“截至2023年12月22日…新能源汽车保有量…万辆”，属2023年末近似口径（非12月31日）。",
    ),
    NevSource(
        province="浙江省",
        year=2023,
        source_id="SRC_CASE02_STRICT_NEV_2023_ZJ",
        source_name="浙江省人民政府-2023年度浙江省文明出行现状发布",
        source_url="https://www.zj.gov.cn/art/2024/1/26/art_1554467_60195319.html",
        publish_date="2024-01-26",
        regex=r"2023年[\s\S]{0,220}?新能源汽车保有量(?:达到|达)([0-9]+(?:\.[0-9]+)?)万辆",
        note="原文明确“2023年…新能源汽车保有量达到…万辆”。",
    ),
    NevSource(
        province="上海市",
        year=2023,
        source_id="SRC_CASE02_STRICT_NEV_2023_SH",
        source_name="上海市人民政府-燃油车以旧换新补贴 新能源汽车置换政策发布",
        source_url="https://www.shanghai.gov.cn/nw4411/20240303/210a0336b8c14e97a6de2c0672d969fc.html",
        publish_date="2024-03-03",
        regex=r"截至2023年末[^。]{0,160}新能源汽车保有量(?:达到|达)([0-9]+(?:\.[0-9]+)?)万辆",
        note="原文明确“截至2023年末…保有量…万辆”。",
    ),
    NevSource(
        province="广东省",
        year=2023,
        source_id="SRC_CASE02_STRICT_NEV_2023_GD",
        source_name="广东省人民政府-广东省节能宣传周启动 去年新能源汽车保有量289万辆",
        source_url="https://www.gd.gov.cn/gdywdt/bmdt/content/post_4422331.html",
        publish_date="2024-05-14",
        regex=r"截至去年底[^。]{0,160}广东新能源汽车保有量(?:达到|达)([0-9]+(?:\.[0-9]+)?)万辆",
        note="原文为“截至去年底…”，结合发布日期 2024-05-14，对应 2023 年底。",
        backup_urls=["http://www.gd.gov.cn/gdywdt/bmdt/content/post_4422331.html"],
    ),
    NevSource(
        province="重庆市",
        year=2023,
        source_id="SRC_CASE02_STRICT_NEV_2023_CQ",
        source_name="重庆市人民政府-重庆2025年底将建成超充站2040座",
        source_url="https://www.cq.gov.cn/zwgk/zfxxgkml/zcjd_120614/mtsj/202405/t20240509_13189834.html",
        publish_date="2024-05-09",
        regex=r"2023年[^。]{0,180}新能源汽车[^。]{0,100}保有量(?:达到|达)([0-9]+(?:\.[0-9]+)?)万辆",
        note="原文明确“2023年…新能源汽车…保有量达到…万辆”。",
    ),
    NevSource(
        province="天津市",
        year=2023,
        source_id="SRC_CASE02_STRICT_NEV_2023_TJ",
        source_name="天津市人民政府-截至7月底 天津市累计建成公共充电桩7.2万台（政民互动回复）",
        source_url="https://www.tj.gov.cn/zmhd/wmfkxd/202408/t20240816_6700013.html",
        publish_date="2024-08-16",
        regex=r"截至2023年底[^。]{0,120}?我市新能源汽车保有量(?:约)?为([0-9]+(?:\.[0-9]+)?)万辆",
        note="天津政务问答页面中答复“经与市工信局了解，截至2023年底，我市新能源汽车保有量约为48万辆”。",
    ),
    NevSource(
        province="湖南省",
        year=2023,
        source_id="SRC_CASE02_STRICT_NEV_2023_HN",
        source_name="湖南省统计局-能源发展新跨越 节能降碳谱新篇",
        source_url="https://tjj.hunan.gov.cn/hntj/tjfx/jmxx/2024sjjd/202409/t20240929_33465665.html",
        publish_date="2024-09-29",
        regex=r"2023年[^。]{0,120}?新能源汽车保有量([0-9]+(?:\.[0-9]+)?)万辆",
        note="省统计局专题文中给出“2023年，新能源汽车保有量56.50万辆”。",
    ),
    NevSource(
        province="广西壮族自治区",
        year=2023,
        source_id="SRC_CASE02_STRICT_NEV_2023_GX",
        source_name="广西壮族自治区人民政府-广西大力实施新能源汽车推广应用提升行动",
        source_url="http://www.gxzf.gov.cn/gxyw/t19439729.shtml",
        publish_date="2024-12-31",
        regex=r"截至11月底[^。]{0,120}?全区新能源汽车保有量(?:达|达到)([0-9]+(?:\.[0-9]+)?)万辆",
        note="原文口径为“截至11月底…保有量…万辆”，属2023年末近似口径（非12月31日）。",
    ),
    NevSource(
        province="海南省",
        year=2023,
        source_id="SRC_CASE02_STRICT_NEV_2023_HI",
        source_name="海南省人民政府-多份提案关注新能源汽车",
        source_url="https://www.hainan.gov.cn/hainan/5309/202401/490e107fee4340c1aacb5edd1f841326.shtml",
        publish_date="2024-01-31",
        regex=r"截至2023年10月底[^。]{0,120}?海南新能源汽车保有量([0-9]+(?:\.[0-9]+)?)万辆",
        note="原文口径为“截至2023年10月底…保有量…万辆”，属2023年内时点口径（非年末）。",
    ),
    NevSource(
        province="安徽省",
        year=2023,
        source_id="SRC_CASE02_STRICT_NEV_2023_AH",
        source_name="安徽省发展改革委-《安徽省新能源汽车充换电基础设施建设运营管理办法（暂行）》政策解读",
        source_url="https://fzggw.ah.gov.cn/public/7011/148994711.html",
        publish_date="2023-12-13",
        regex=r"截至\s*2023\s*年\s*11\s*月\s*底[^。]{0,160}?我省新能源汽车保有量(?:达到|达|为|约为)?\s*([0-9]+(?:\.[0-9]+)?)\s*万辆",
        note="原文明确“截至2023年11月底，我省新能源汽车保有量达到60.3万辆”，属2023年末近似口径（非12月31日）。",
    ),
    NevSource(
        province="山东省",
        year=2023,
        source_id="SRC_CASE02_STRICT_NEV_2023_SD",
        source_name="山东省能源局-《山东省电动汽车充电基础设施发展白皮书》发布",
        source_url="http://nyj.shandong.gov.cn/art/2023/12/2/art_59966_10301975.html",
        publish_date="2023-12-02",
        regex=r"新能源汽车保有量\s*([0-9]+(?:\.[0-9]+)?)\s*万辆",
        note="原文给出“截至2023年9月底…新能源汽车保有量165.9万辆”，属2023年内时点口径（非年末）。",
    ),
    NevSource(
        province="河北省",
        year=2023,
        source_id="SRC_CASE02_STRICT_NEV_2023_HE",
        source_name="河北省工信厅-关于2023年工业领域生态环境保护工作情况的报告",
        source_url="https://gxt.hebei.gov.cn/hbgyhxxht/zfxxgk/fdzdgknr/gzdt68/tzgg9917/2025042121501226167/index.html",
        publish_date="2025-04-21",
        regex=r"2023年[^。]{0,220}?新能源(?:汽车|车)推广[0-9]+(?:\.[0-9]+)?万辆[^。]{0,120}?保有量(?:达到|达|为)\s*([0-9]+(?:\.[0-9]+)?)\s*万辆",
        note="原文给出“2023年，全年新能源车推广30.4万辆，保有量达到80.8万辆”。",
    ),
    NevSource(
        province="河南省",
        year=2023,
        source_id="SRC_CASE02_STRICT_NEV_2023_HA",
        source_name="河南省住建厅-对省十四届人大二次会议第858号建议的答复",
        source_url="https://hnjs.henan.gov.cn/2024/08-12/3035341.html",
        publish_date="2024-08-12",
        regex=r"截至\s*2023\s*年底[^。]{0,180}?我省电动汽车保有量(?:达到|达|为|约为)?\s*([0-9]+(?:\.[0-9]+)?)\s*万辆",
        note="原文给出“截至2023年底，我省电动汽车保有量达到114万辆”；该来源为“电动汽车”口径，可能与“新能源汽车”统计口径存在差异。",
    ),
    NevSource(
        province="四川省",
        year=2023,
        source_id="SRC_CASE02_STRICT_NEV_2023_SC",
        source_name="四川省人民政府-@新能源车主，四川将这样缓解你的“里程焦虑”",
        source_url="https://www.sc.gov.cn/10462/10464/13298/13299/2024/6/28/08e35bde8718453d9a27934e8c9bea17.shtml",
        publish_date="2024-06-28",
        regex=r"四川省电动汽车保有量[^。]{0,120}?2023年底[^。]{0,80}?(?:达|达到)\s*([0-9]+(?:\.[0-9]+)?)\s*万辆",
        note="原文给出“四川省电动汽车保有量快速增长，2023年底数量达89.63万辆”；该来源为“电动汽车”口径，可能与“新能源汽车”统计口径存在差异。",
    ),
    NevSource(
        province="云南省",
        year=2023,
        source_id="SRC_CASE02_STRICT_NEV_2023_YN",
        source_name="云南省能源局-《云南省推进新能源发展工作情况》政策解读",
        source_url="https://nyj.yn.gov.cn/nyj_file/html/xzgfwjjd/2024/1217/000027.html",
        publish_date="2024-12-22",
        regex=r"2023年10月底[^。]{0,120}?我省新能源汽车保有量(?:达到|达|为|约为)?\s*([0-9]+(?:\.[0-9]+)?)\s*万辆",
        note="原文给出“2023年10月底，我省新能源汽车保有量达到32.6万辆”，属2023年内时点口径（非年末）。",
    ),
    NevSource(
        province="内蒙古自治区",
        year=2023,
        source_id="SRC_CASE02_STRICT_NEV_2023_NM",
        source_name="巴彦淖尔市科技局-前三季度全区累计推广应用新能源汽车27850辆（转载）",
        source_url="http://kjj.bynr.gov.cn/kjxx/gnkj/202311/t20231114_574040_senior.html",
        publish_date="2023-11-14",
        regex=r"截至今年9月30日[^。]{0,140}?全区新能源汽车保有量(?:为|达|达到)?\s*([0-9]+(?:\.[0-9]+)?)\s*辆",
        note="巴彦淖尔市科技局转载稿原文给出“截至今年9月30日，全区新能源汽车保有量为82998辆”；值为“辆”，已换算为“万辆”（÷10000）。属2023年内时点口径（非年末）。",
        scale_to_10k=0.0001,
        backup_urls=["https://www.nmg.gov.cn/zfbgt/zwxx/202311/t20231114_2410054.html"],
    ),
    NevSource(
        province="陕西省",
        year=2023,
        source_id="SRC_CASE02_STRICT_NEV_2023_SN",
        source_name="陕西省人民政府-如何缓解新能源汽车“里程焦虑”？",
        source_url="https://www.shaanxi.gov.cn/xw/sxyw/202308/t20230811_2296960_wap.html",
        publish_date="2023-08-11",
        regex=r"目前[^。]{0,120}?我省电动汽车保有量(?:达到|达|为)?\s*([0-9]+(?:\.[0-9]+)?)\s*万辆",
        note="原文给出“目前，我省电动汽车保有量39.77万辆，全国排名第16位”；属2023年内时点口径（非年末），且为“电动汽车”口径。",
    ),
    NevSource(
        province="新疆维吾尔自治区",
        year=2023,
        source_id="SRC_CASE02_STRICT_NEV_2023_XJ",
        source_name="新疆维吾尔自治区人民政府-新疆首批“光储充放”一体化试点项目并网",
        source_url="https://www.xinjiang.gov.cn/xinjiang/bmdt/202310/2339a216530641b7adab3da6bd6bbe48.shtml",
        publish_date="2023-10-18",
        regex=r"目前新疆新能源汽车保有量(?:在)?\s*([0-9]+(?:\.[0-9]+)?)\s*万辆",
        note="原文给出“目前新疆新能源汽车保有量在5万辆左右，并逐年增加”；属2023年内时点口径（非年末）。",
    ),
    NevSource(
        province="江苏省",
        year=2023,
        source_id="SRC_CASE02_STRICT_NEV_2023_JS",
        source_name="江苏省政协-关于在大力推动充电桩建设的同时加强安全监管的提案",
        source_url="http://www.jszx.gov.cn/wylz/zxta/2023ta/202301/t20230116_94117.html",
        publish_date="2023-01-16",
        regex=r"目前[^。]{0,80}?我省电动汽车保有量\s*([0-9]+(?:\.[0-9]+)?)\s*万辆",
        note="江苏省政协提案页面原文给出“目前，我省电动汽车保有量33.4万辆”；属2023年年初时点口径（非年末），且为“电动汽车”口径。",
    ),
    NevSource(
        province="宁夏回族自治区",
        year=2023,
        source_id="SRC_CASE02_STRICT_NEV_2023_NX",
        source_name="银川市人民政府-截至9月底 宁夏机动车保有量达226万辆",
        source_url="https://yinchuan.gov.cn/xwzx/mrdt/202311/t20231101_4335710.html",
        publish_date="2023-11-01",
        regex=r"截至9月底[^。]{0,140}?宁夏新能源汽车保有量(?:达|达到|为)?\s*([0-9]+(?:\.[0-9]+)?)\s*万辆",
        note="银川市政府转载公安交管统计口径，原文给出“截至9月底，宁夏新能源汽车保有量达4.3万辆”，属2023年内时点口径（非年末）。",
    ),
    NevSource(
        province="山西省",
        year=2023,
        source_id="SRC_CASE02_STRICT_NEV_2023_SX",
        source_name="山西省人民政府-让出行更加便捷绿色低碳",
        source_url="http://www.shanxi.gov.cn/ywdt/sxyw/202308/t20230807_9078335.shtml",
        publish_date="2023-08-07",
        regex=r"截至目前[^。]{0,120}?我省[^。]{0,120}?新能源汽车保有量(?:约)?\s*([0-9]+(?:\.[0-9]+)?)\s*万辆",
        note="原文给出“截至目前，我省…新能源汽车保有量约34.64万辆”；发布日期为2023-08-07，属2023年内时点口径（非年末）。",
    ),
]


def _fetch_once(url: str) -> str:
    try:
        resp = requests.get(url, timeout=35, headers={"User-Agent": "Mozilla/5.0"})
    except SSLError:
        resp = requests.get(url, timeout=35, headers={"User-Agent": "Mozilla/5.0"}, verify=False)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding or "utf-8"
    text = BeautifulSoup(resp.text, "html.parser").get_text(" ")
    text = re.sub(r"\s+", " ", text)
    if "很抱歉，您所访问的页面不存在" in text and len(text) < 300:
        raise RuntimeError("fetched anti-bot/404 placeholder page")
    return text


def fetch_text(urls: list[str], retries: int = 3) -> str:
    last_err: Exception | None = None
    dedup = []
    seen = set()
    for u in urls:
        if u and u not in seen:
            seen.add(u)
            dedup.append(u)
    for i in range(retries):
        for u in dedup:
            try:
                return _fetch_once(u)
            except Exception as e:
                last_err = e
        if i < retries - 1:
            time.sleep(1.2 * (i + 1))
    raise RuntimeError(f"all urls failed after retries, last_error={last_err}")


def extract_value_and_evidence(text: str, pattern: str) -> tuple[float, str] | None:
    m = re.search(pattern, text)
    if not m:
        return None
    val = float(m.group(1))
    frag = re.sub(r"\s+", " ", m.group(0)).strip()
    k = frag.find("新能源汽车保有量")
    evidence = frag[max(0, k - 28) : min(len(frag), k + 40)] if k >= 0 else frag
    evidence = evidence.strip(" ，,。;；")
    return val, evidence


def write_partial_csv(rows: list[dict]) -> None:
    fields = [
        "province",
        "year",
        "nev_stock_10k",
        "source_id",
        "source_name",
        "source_url",
        "publish_date",
        "evidence",
        "note",
    ]
    with NEV_OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def merge_with_existing_rows(new_rows: list[dict]) -> list[dict]:
    merged: dict[tuple[str, int], dict] = {}
    if NEV_OUT.exists():
        for r in csv.DictReader(NEV_OUT.open("r", encoding="utf-8-sig")):
            key = ((r.get("province") or "").strip(), int((r.get("year") or "0").strip() or 0))
            if key[0] and key[1]:
                merged[key] = r
    for r in new_rows:
        key = (r["province"], int(r["year"]))
        merged[key] = r
    return sorted(merged.values(), key=lambda x: (x["province"], int(x["year"])))


def update_panel(rows: list[dict]) -> None:
    panel = list(csv.DictReader(PANEL_PATH.open("r", encoding="utf-8-sig")))
    idx = {(r["province"], int(r["year"])): r for r in panel}
    for row in rows:
        key = (row["province"], int(row["year"]))
        if key in idx:
            idx[key]["nev_stock_10k"] = f"{row['nev_stock_10k']}"
    fields = panel[0].keys()
    with PANEL_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(panel)


def update_source_registry(rows: list[dict]) -> None:
    reg_rows = list(csv.DictReader(REG_PATH.open("r", encoding="utf-8-sig")))
    exists = {r["source_id"] for r in reg_rows}
    access_date = date.today().isoformat()
    for r in rows:
        if r["source_id"] in exists:
            continue
        reg_rows.append(
            {
                "source_id": r["source_id"],
                "variable": "nev_stock_10k",
                "source_level": "A",
                "source_name": r["source_name"],
                "source_url": r["source_url"],
                "cross_check_url": "",
                "publish_date": r["publish_date"],
                "access_date": access_date,
                "evidence_file": "nev_stock_strict_2023_partial.csv",
                "is_primary": "1",
                "note": r["note"],
            }
        )
    fields = reg_rows[0].keys()
    with REG_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(reg_rows)


def summarize_panel_2023() -> None:
    panel = list(csv.DictReader(PANEL_PATH.open("r", encoding="utf-8-sig")))
    rows = [r for r in panel if (r.get("year") or "").strip() == "2023"]
    all_prov = sorted({r["province"] for r in rows})
    filled = sorted([r["province"] for r in rows if (r.get("nev_stock_10k") or "").strip()])
    miss = [p for p in all_prov if p not in filled]
    print(f"[SUMMARY] 2023 strict coverage: {len(filled)}/{len(all_prov)}")
    print(f"[SUMMARY] filled: {'、'.join(filled)}")
    if miss:
        print(f"[SUMMARY] missing({len(miss)}): {'、'.join(miss)}")
    else:
        print("[SUMMARY] missing(0): -")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out_rows: list[dict] = []

    for src in SOURCES:
        try:
            text = fetch_text([src.source_url] + (src.backup_urls or []))
            got = extract_value_and_evidence(text, src.regex)
            if not got:
                print(f"[MISS] {src.province}: regex not matched")
                continue
            value, evidence = got
            value_10k = value * src.scale_to_10k
            out_rows.append(
                {
                    "province": src.province,
                    "year": src.year,
                    "nev_stock_10k": value_10k,
                    "source_id": src.source_id,
                    "source_name": src.source_name,
                    "source_url": src.source_url,
                    "publish_date": src.publish_date,
                    "evidence": evidence,
                    "note": src.note,
                }
            )
            print(f"[OK] {src.province} {src.year}: {value_10k} 万辆")
        except Exception as e:
            print(f"[ERR] {src.province}: {e}")

    merged_rows = merge_with_existing_rows(out_rows)
    write_partial_csv(merged_rows)
    if out_rows:
        update_panel(out_rows)
        update_source_registry(out_rows)

    print(f"saved: {NEV_OUT} rows={len(merged_rows)} (new_this_run={len(out_rows)})")
    summarize_panel_2023()


if __name__ == "__main__":
    main()
