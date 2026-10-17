# -*- coding: utf-8 -*-
"""《鸣潮》动作帧拆解 03：削韧值。

一个动作削掉对方多少韧性，决定了破韧快慢。

用法:
    python deconstructions/poise.py <动作数据表.xlsx> --json out.json
"""
from __future__ import annotations

import io
import json
import sys
from collections import Counter

from _shared import load_actions

# 表里出现的一些明显是哨兵值（表示「削满」或占位），统计时要单独处理
SENTINEL = 10000.0

CATEGORY = [
    ("普攻", ("普攻", "A1", "A2", "A3", "A4", "A5", "A6")),
    ("重击", ("重击",)),
    ("共鸣技能", ("E", "共鸣技能", "强化E")),
    ("共鸣解放", ("大招", "共鸣解放", "解放")),
    ("变奏/延奏", ("变奏", "延奏", "同奏")),
    ("闪避/反击", ("闪避", "反击")),
]


def category_of(action: str) -> str:
    for label, keys in CATEGORY:
        if any(k in action for k in keys):
            return label
    return "其他"


def analyse(rows):
    vals = [r["poise"] for r in rows if r["poise"]]
    normal = [v for v in vals if 0 < v < SENTINEL]
    sentinels = [v for v in vals if v >= SENTINEL]

    by_cat = {}
    for label, _ in CATEGORY:
        by_cat[label] = []
    for r in rows:
        v = r["poise"]
        if v is None or v <= 0 or v >= SENTINEL:
            continue
        by_cat.setdefault(category_of(r["action"]), []).append(v)

    cat_rows = []
    for label in sorted(by_cat, key=lambda k: -len(by_cat[k])):
        arr = by_cat.get(label) or []
        if not arr:
            continue
        arr_sorted = sorted(arr)
        cat_rows.append({
            "category": label,
            "count": len(arr),
            "median": round(arr_sorted[len(arr_sorted) // 2], 1),
            "max": max(arr),
        })
    cat_rows.sort(key=lambda x: -x["median"])

    exact = Counter(round(v, 1) for v in normal)
    return {
        "row_count": len(rows),
        "with_poise": len(vals),
        "normal": len(normal),
        "sentinels": len(sentinels),
        "median": sorted(normal)[len(normal) // 2] if normal else None,
        "max_normal": max(normal) if normal else None,
        "common": [{"value": v, "count": n} for v, n in exact.most_common(12)],
        "by_category": cat_rows,
        "top_actions": [
            {"action": r["action"], "value": r["poise"], "cat": category_of(r["action"])}
            for r in sorted([x for x in rows if x["poise"] and 0 < x["poise"] < SENTINEL],
                            key=lambda x: -x["poise"])[:10]
        ],
    }


def main():
    xlsx = sys.argv[1] if len(sys.argv) > 1 else r"data\鸣潮动作数据汇总.xlsx"
    res = analyse(load_actions(xlsx))

    if "--json" in sys.argv:
        path = sys.argv[sys.argv.index("--json") + 1]
        io.open(path, "w", encoding="utf-8").write(
            json.dumps(res, ensure_ascii=False, indent=1))

    L = [
        "动作 %d 个，带削韧值 %d 个（正常 %d，哨兵值 %d）"
        % (res["row_count"], res["with_poise"], res["normal"], res["sentinels"]),
        "中位数 %s，最大值 %s" % (res["median"], res["max_normal"]),
        "",
        "== 按动作类型 ==",
    ]
    for c in res["by_category"]:
        L.append("  %-10s %4d 条  中位 %6.1f  最高 %6.1f"
                 % (c["category"], c["count"], c["median"], c["max"]))
    L.append("")
    L.append("== 最常见取值 ==")
    for c in res["common"]:
        L.append("  %6.1f  %3d 条" % (c["value"], c["count"]))
    L.append("")
    L.append("== 单次削韧最高 ==")
    for t in res["top_actions"]:
        L.append("  %-24s %7.1f  [%s]" % (t["action"], t["value"], t["cat"]))
    io.open("data/_poise_summary.txt", "w", encoding="utf-8").write("\n".join(L))
    print("ok")


if __name__ == "__main__":
    main()
