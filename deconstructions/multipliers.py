# -*- coding: utf-8 -*-
"""《鸣潮》角色拆解 10：技能倍率的横向结构。

只看一件事：60 个角色，谁的技能倍率总量高，倍率又是怎么分配到不同技能上的。

用法:
    python deconstructions/multipliers.py <zh_character 目录> --json out.json
"""
from __future__ import annotations

import glob
import io
import json
import os
import re
import sys
from collections import defaultdict

TERM = re.compile(r"([\d.]+)\s*%\s*(?:\*\s*(\d+))?")

SKILL_TYPE = {
    "常态攻击": "普攻",
    "共鸣技能": "技能",
    "共鸣解放": "解放",
    "变奏技能": "变奏",
    "共鸣回路": "回路",
    "延奏技能": "延奏",
}


def eval_expr(text: str):
    if not isinstance(text, str) or "%" not in text:
        return None
    total, hit = 0.0, False
    for m in TERM.finditer(text):
        total += float(m.group(1)) / 100.0 * (int(m.group(2)) if m.group(2) else 1)
        hit = True
    return total if hit else None


def load_dir(path: str):
    out = []
    for fp in glob.glob(os.path.join(path, "*.json")):
        try:
            d = json.load(io.open(fp, encoding="utf-8"))
        except Exception:
            continue
        name = d.get("name")
        if not name and isinstance(d.get("zh"), dict):
            name = d.get("zh", {}).get("name")
        name = name or d.get("id")
        skills = d.get("skill_trees") or {}
        by_type = defaultdict(float)
        total = 0.0
        found = 0
        for node in skills.values():
            sk = node.get("skill") or {}
            stype = SKILL_TYPE.get(sk.get("type") or "", "其他")
            for lv_name, lv in (sk.get("level") or {}).items():
                params = lv.get("param") or []
                if not params or not params[0]:
                    continue
                raw = params[0]
                if len(raw) < 10:          # 不足 10 级的不参与
                    continue
                v = eval_expr(str(raw[9]))  # 第 10 级
                if v is None:
                    continue
                by_type[stype] += v
                total += v
                found += 1
        if found:
            out.append({"name": name, "total": round(total, 3),
                        "by_type": {k: round(v, 3) for k, v in by_type.items()},
                        "count": found})
    return out


def analyse(chars):
    chars.sort(key=lambda c: -c["total"])
    totals = [c["total"] for c in chars]
    types = defaultdict(float)
    for c in chars:
        for k, v in c["by_type"].items():
            types[k] += v
    n = len(chars) or 1
    return {
        "characters": len(chars),
        "median_total": sorted(totals)[len(totals) // 2] if totals else None,
        "min": min(totals) if totals else None,
        "max": max(totals) if totals else None,
        "share_by_type": {k: round(v / sum(types.values()) * 100, 1)
                          for k, v in sorted(types.items(), key=lambda kv: -kv[1])},
        "top": chars[:8],
        "bottom": chars[-8:],
    }


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else r"data\nanoka\3.7\zh_character"
    res = analyse(load_dir(path))

    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
        io.open(out, "w", encoding="utf-8").write(
            json.dumps(res, ensure_ascii=False, indent=1))

    L = ["角色 %d 个" % res["characters"],
         "全员技能倍率总和（10 级）中位 %.2f，范围 %.2f～%.2f"
         % (res["median_total"], res["min"], res["max"]), "",
         "== 倍率按技能类型分配 =="]
    for k, v in res["share_by_type"].items():
        L.append("  %-6s %5.1f%%" % (k, v))
    L.append("")
    L.append("== 总和最高的 8 个 ==")
    for c in res["top"]:
        L.append("  %-8s %6.2f" % (c["name"], c["total"]))
    L.append("")
    L.append("== 总和最低的 8 个 ==")
    for c in res["bottom"]:
        L.append("  %-8s %6.2f" % (c["name"], c["total"]))
    io.open("data/_mult_summary.txt", "w", encoding="utf-8").write("\n".join(L))
    print("ok")


if __name__ == "__main__":
    main()
