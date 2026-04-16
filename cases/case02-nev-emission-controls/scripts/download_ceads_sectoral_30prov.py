#!/usr/bin/env python3
"""
下载 CEADs 2012-2022「30个省份排放清单」。

依赖：
- 环境变量 CEADS_USERNAME / CEADS_PASSWORD
- 如存在上级 `math` 项目，则复用其中的 `login_ceads`（含验证码 OCR）
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
from pathlib import Path
from urllib.parse import unquote

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = ROOT / "cases" / "case02-nev-emission-controls" / "data" / "raw_ceads_sectoral_30prov"
MATH_LOGIN_SCRIPT = ROOT.parent / "math" / "ceads_download_and_extract.py"


def _load_login_func():
    spec = importlib.util.spec_from_file_location("ceads_mod", MATH_LOGIN_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod.login_ceads


def parse_target_ids() -> list[dict]:
    resp = requests.get("https://www.ceads.net.cn/data/province/", timeout=40)
    resp.encoding = "utf-8"
    soup = BeautifulSoup(resp.text, "html.parser")

    rows = []
    for box in soup.select("div.feature-box"):
        a_title = box.select_one("h4 a")
        a_dl = box.select_one("div.feature-box-icon a[data-id]")
        if not a_title or not a_dl:
            continue
        title = a_title.get_text(strip=True)
        did = a_dl.get("data-id")
        if not did:
            continue
        if "30个省份排放清单" not in title:
            continue
        m = re.search(r"(20\d{2})", title)
        if not m:
            continue
        year = int(m.group(1))
        if 2012 <= year <= 2022:
            rows.append({"id": did, "year": year, "title": title})
    return sorted(rows, key=lambda x: x["year"])


def main() -> None:
    username = os.environ.get("CEADS_USERNAME", "").strip()
    password = os.environ.get("CEADS_PASSWORD", "").strip()
    if not username or not password:
        raise RuntimeError("请设置 CEADS_USERNAME / CEADS_PASSWORD")
    if not MATH_LOGIN_SCRIPT.exists():
        raise FileNotFoundError(f"未找到登录脚本: {MATH_LOGIN_SCRIPT}")

    login_ceads = _load_login_func()
    sess, info = login_ceads(username, password, redirect_id=1454, max_attempts=30)
    if not info.get("success"):
        raise RuntimeError(f"CEADs 登录失败: {info}")

    targets = parse_target_ids()
    if not targets:
        raise RuntimeError("未解析到 2012-2022 的 30省排放清单ID")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    logs = []
    for t in targets:
        did = t["id"]
        year = t["year"]
        url = f"https://www.ceads.net/user/dl.php?id={did}&lang=cn"
        r = sess.get(url, timeout=90, allow_redirects=True)
        cd = r.headers.get("content-disposition", "")
        ct = r.headers.get("content-type", "")
        rec = {
            "id": did,
            "year": year,
            "title": t["title"],
            "status_code": r.status_code,
            "final_url": r.url,
            "content_type": ct,
            "content_disposition": cd,
            "size": len(r.content),
        }
        if "login.php" in r.url:
            rec["error"] = "redirected_to_login"
            logs.append(rec)
            print(f"[WARN] {year}: redirected to login")
            continue

        fname = ""
        m = re.search(r"filename\*?=(?:UTF-8''|\")?([^\";]+)", cd)
        if m:
            fname = unquote(m.group(1))
        if not fname:
            fname = f"{year}年30个省份排放清单.xlsx"
        if not fname.lower().endswith((".xlsx", ".xls")):
            fname = f"{year}年30个省份排放清单.xlsx"
        fname = fname.replace("/", "_").replace("\\", "_")
        out = OUT_DIR / fname
        out.write_bytes(r.content)
        rec["saved"] = str(out)
        logs.append(rec)
        print(f"[OK] {year}: {out.name}")

    log_path = OUT_DIR / "download_log.json"
    log_path.write_text(json.dumps(logs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[DONE] {log_path}")


if __name__ == "__main__":
    main()
