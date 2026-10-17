# -*- coding: utf-8 -*-
"""《鸣潮》角色拆解 13：充能预算。

不同消耗档的角色，技能组给的固定充能是不是按比例补偿的。

用法:
    python deconstructions/energy_budget.py <zh_character 目录> --json out.json
"""
from __future__ import annotations

import glob
import io
import json
import os
import sys
from collections import defaultdict

ULT_TO_CONCERTO = 0.5     # 第 12 篇推出的比值


def load(path):
    rows = []
    for fp in glob.glob(os.path.join(path, "*.json")):
        try:
            d = json.load(io.open(fp, encoding="utf-8"))
        except Exception:
            continue
        name = d.get("name") or d.get("id")
        conc = 0.0
        cost = None
        for node in (d.get("skill_trees") or {}).values():
            sk = node.get("skill") or {}
            for lv in (sk.get("level") or {}).values():
                label = str(lv.get("name") or "")
                p = lv.get("param") or [[]]
                first = p[0][0] if p and p[0] else None
                if "消耗共鸣能量" in label:
                    try:
                        cost = float(str(first))
                    except (TypeError, ValueError):
                        pass
                elif "回复协奏能量" in label:
                    try:
                        conc += float(str(first))
                    except (TypeError, ValueError):
                        pass
        if cost and conc:
            rows.append({"name": name, "cost": cost, "concerto": round(conc, 1)})
    return rows


def analyse(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[r["cost"]].append(r["concerto"])

    table = []
    for cost in sorted(groups):
        vals = sorted(groups[cost])
        med = vals[len(vals) // 2]
        table.append({
            "cost": cost,
            "count": len(vals),
            "median_concerto": med,
            "ult_energy": round(med * ULT_TO_CONCERTO, 1),
            "coverage": round(med * ULT_TO_CONCERTO / cost * 100, 1),
        })

    return {"characters": len(rows), "ratio": ULT_TO_CONCERTO,
            "by_cost": table, "rows": rows}


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else r"data\nanoka\3.7\zh_character"
    res = analyse(load(path))

    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
        io.open(out, "w", encoding="utf-8").write(
            json.dumps(res, ensure_ascii=False, indent=1))

    L = ["角色 %d 个，大招/协奏比值 %.1f" % (res["characters"], res["ratio"]),
         "", "消耗 | 人数 | 协奏回复中位 | 折成大招能量 | 占需求"]
    for r in res["by_cost"]:
        L.append("%5.0f | %3d | %6.1f | %6.1f | %5.1f%%"
                 % (r["cost"], r["count"], r["median_concerto"],
                    r["ult_energy"], r["coverage"]))
    io.open(os.path.join("data", "_energy_budget.txt"), "w",
            encoding="utf-8").write("\n".join(L))
    print("ok")


if __name__ == "__main__":
    main()
