#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Planner：将变量清单自动路由到执行链路（借鉴 GPT-Researcher 的 planner 思路）。

输入：research spec JSON
输出：plan JSON + Markdown（四阶段：Planner/Executor/Extractor/Validator）
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


@dataclass
class VariableItem:
    name: str
    name_cn: str
    unit: str
    source_hint: str
    note: str


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="根据变量清单生成标准四阶段搜集计划")
    p.add_argument("--spec-file", required=True, help="研究任务规格 JSON")
    p.add_argument("--out-json", default="", help="计划输出 JSON")
    p.add_argument("--out-md", default="", help="计划输出 Markdown")
    return p.parse_args()


def load_spec(path: Path) -> Dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("spec root must be object")
    if "variables" not in data or not isinstance(data["variables"], list):
        raise ValueError("spec must include variables:list")
    return data


def classify_route(v: VariableItem) -> str:
    t = f"{v.name} {v.name_cn} {v.source_hint} {v.note}".lower()
    api_kw = ["api", "akshare", "nbs", "stats.gov", "数据库", "接口", "json"]
    doc_kw = ["excel", "xlsx", "csv", "pdf", "年鉴", "公报", "ceads", "报告", "附件"]
    dynamic_kw = ["动态", "js", "javascript", "分页", "搜索", "官网", "公告", "详情页", "爬取"]
    local_kw = ["local", "本地", "file", "文档", "docx", "ppt", "txt"]
    if any(k in t for k in api_kw):
        return "api"
    if any(k in t for k in doc_kw):
        return "doc_or_table"
    if any(k in t for k in dynamic_kw):
        return "dynamic_web"
    if any(k in t for k in local_kw):
        return "local_docs"
    return "web_search"


def build_plan(spec: Dict) -> Dict:
    vars_in: List[VariableItem] = []
    for it in spec.get("variables", []):
        if not isinstance(it, dict):
            continue
        vars_in.append(
            VariableItem(
                name=str(it.get("name") or "").strip(),
                name_cn=str(it.get("name_cn") or "").strip(),
                unit=str(it.get("unit") or "").strip(),
                source_hint=str(it.get("source_hint") or "").strip(),
                note=str(it.get("note") or "").strip(),
            )
        )

    routed = []
    groups: Dict[str, List[Dict]] = defaultdict(list)
    for v in vars_in:
        route = classify_route(v)
        row = {
            "name": v.name,
            "name_cn": v.name_cn,
            "unit": v.unit,
            "source_hint": v.source_hint,
            "route": route,
        }
        routed.append(row)
        groups[route].append(row)

    strict = bool(spec.get("strict_mode", False))
    engine_stack = spec.get("engine_stack") or ["google", "tavily", "bing", "sogou", "360"]
    mcp_stack = spec.get("mcp_stack") or ["tavily-proxy", "exa-proxy"]

    plan = {
        "topic": spec.get("topic", ""),
        "scope": {
            "geography": spec.get("geography", ""),
            "time_range": spec.get("time_range", ""),
            "strict_mode": strict,
        },
        "planner": {
            "objective": "将变量按来源形态路由到最优执行器，优先官方与可审计来源",
            "routing_result": routed,
            "engine_stack": engine_stack,
            "mcp_stack": mcp_stack,
        },
        "executor": {
            "api_executor": {
                "enabled": len(groups["api"]) > 0,
                "variables": groups["api"],
                "tools": ["requests", "akshare", "官方API脚本"],
            },
            "browser_executor": {
                "enabled": len(groups["dynamic_web"]) + len(groups["web_search"]) > 0,
                "variables": groups["dynamic_web"] + groups["web_search"],
                "tools": ["Camoufox/Playwright", "多引擎搜索", "MCP搜索(Tavily/Exa)"],
            },
            "doc_executor": {
                "enabled": len(groups["doc_or_table"]) + len(groups["local_docs"]) > 0,
                "variables": groups["doc_or_table"] + groups["local_docs"],
                "tools": ["PDF/Excel解析", "schema抽取", "markdown归档"],
            },
        },
        "extractor": {
            "strategy": [
                "优先 schema/regex 提取（可复现）",
                "复杂页面使用 LLM 辅助抽取并保留 evidence 片段",
                "统一输出 JSON/CSV 字段",
            ],
            "output_fields": ["value", "unit", "year", "entity", "source_url", "evidence", "note"],
        },
        "validator_synthesizer": {
            "qc_rules": [
                "主键唯一（如 province+year）",
                "单位统一并记录换算",
                "来源分级 + access_date + source_url",
                "生成 panel + source_registry + search_log",
            ],
            "missing_policy": "strict留空" if strict else "可估算但需单独标注",
            "interpolation": False if strict else True,
            "deliverables": ["panel.csv/xlsx", "source_registry.csv", "progress-report.md"],
        },
    }
    return plan


def render_md(plan: Dict) -> str:
    lines: List[str] = []
    lines.append("# 研究工作流计划（Planner 生成）")
    lines.append("")
    lines.append(f"- 主题：{plan.get('topic','')}")
    scope = plan.get("scope", {})
    lines.append(f"- 范围：{scope.get('geography','')} | {scope.get('time_range','')}")
    lines.append(f"- strict_mode：{scope.get('strict_mode')}")
    lines.append("")
    lines.append("## 1) Planner 路由结果")
    for r in plan.get("planner", {}).get("routing_result", []):
        lines.append(
            f"- `{r.get('name')}` / {r.get('name_cn')} -> **{r.get('route')}** "
            f"(hint: {r.get('source_hint')})"
        )
    lines.append("")
    lines.append("## 2) Executor")
    ex = plan.get("executor", {})
    for k in ["api_executor", "browser_executor", "doc_executor"]:
        obj = ex.get(k, {})
        lines.append(f"### {k}")
        lines.append(f"- enabled: {obj.get('enabled')}")
        lines.append(f"- tools: {', '.join(obj.get('tools', []))}")
        lines.append(f"- vars: {len(obj.get('variables', []))}")
    lines.append("")
    lines.append("## 3) Extractor")
    for s in plan.get("extractor", {}).get("strategy", []):
        lines.append(f"- {s}")
    lines.append("")
    lines.append("## 4) Validator & Synthesizer")
    val = plan.get("validator_synthesizer", {})
    for q in val.get("qc_rules", []):
        lines.append(f"- {q}")
    lines.append(f"- missing_policy: {val.get('missing_policy')}")
    lines.append(f"- interpolation: {val.get('interpolation')}")
    lines.append("")
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    args = parse_args()
    spec_path = Path(args.spec_file)
    spec = load_spec(spec_path)
    plan = build_plan(spec)

    out_json = Path(args.out_json) if args.out_json else spec_path.with_name(spec_path.stem + ".plan.json")
    out_md = Path(args.out_md) if args.out_md else spec_path.with_name(spec_path.stem + ".plan.md")
    out_json.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    out_md.write_text(render_md(plan), encoding="utf-8")
    print(f"[DONE] json={out_json} md={out_md}")


if __name__ == "__main__":
    main()

