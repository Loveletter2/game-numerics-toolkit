# -*- coding: utf-8 -*-
"""《鸣潮》动作帧拆解 02：协奏能量的来源结构。

只看一件事：协奏能量是从哪些动作里来的，一次给多少。

用法:
    python deconstructions/energy.py <动作数据表.xlsx> --json out.json
"""
from __future__ import annotations

import io
import json
import sys
from collections import Counter

from _shared import load_actions

CONCERTO_CAP = 100     # 攒满一次协奏（可换人）

BUCKETS = [
    (-1e9, 0.0, "≤0（消耗）"),
    (0.0, 1.0, "0～1"),
    (1.0, 2.0, "1～2"),
    (2.0, 5.0, "2～5"),
    (5.0, 10.0, "5～10"),
    (10.0, 20.0, "10～20"),
    (20.0, 50.0, "20～50"),
    (50.0, 1e9, ">50"),
]


def bucket_of(v: float) -> str:
    for lo, hi, label in BUCKETS:
        if lo < v <= hi:
            return label
    return BUCKETS[0][2]


def analyse(rows):
    vals = [r["concerto"] for r in rows if r["concerto"]]
    positive = [v for v in vals if v > 0]
    negative = [v for v in vals if v <= 0]

    counts = Counter(round(v, 3) for v in vals)
    buckets = Counter(bucket_of(v) for v in vals)

    # 只保留数量 >=3 的「常见档位」，避免浮点噪声
    common = [(v, n) for v, n in counts.most_common(14) if n >= 3]

    return {
        "row_count": len(rows),
        "with_concerto": len(vals),
        "positive": len(positive),
        "negative": len(negative),
        "buckets": {label: buckets.get(label, 0) for _, _, label in BUCKETS},
        "common_values": [{"value": v, "count": n} for v, n in common],
        "top_actions": [
            {"action": r["action"], "value": r["concerto"]}
            for r in sorted([x for x in rows if x["concerto"]],
                            key=lambda x: -x["concerto"])[:8]
        ],
        "negative_actions": [
            {"action": r["action"], "value": r["concerto"]}
            for r in sorted([x for x in rows if x["concerto"] and x["concerto"] <= 0],
                            key=lambda x: x["concerto"])[:8]
        ],
        "concerto_cap": CONCERTO_CAP,
    }


def main():
    xlsx = sys.argv[1] if len(sys.argv) > 1 else r"data\鸣潮动作数据汇总.xlsx"
    res = analyse(load_actions(xlsx))

    if "--json" in sys.argv:
        path = sys.argv[sys.argv.index("--json") + 1]
        io.open(path, "w", encoding="utf-8").write(
            json.dumps(res, ensure_ascii=False, indent=1))

    L = [
        "动作 %d 个，其中给协奏能量的 %d 个（%d 个为正，%d 个为零或负）"
        % (res["row_count"], res["with_concerto"],
           res["positive"], res["negative"]),
        "",
        "== 按档位分布 ==",
    ]
    for label, n in res["buckets"].items():
        if n:
            L.append("  %-12s %4d 条" % (label, n))
    L.append("")
    L.append("== 最常见的单次值 ==")
    for c in res["common_values"]:
        L.append("  %6.1f  %3d 条" % (c["value"], c["count"]))
    L.append("")
    L.append("== 单次给得最多的动作 ==")
    for t in res["top_actions"]:
        L.append("  %-24s %5.1f" % (t["action"], t["value"]))
    L.append("")
    L.append("== 负数（消耗）==")
    for t in res["negative_actions"]:
        L.append("  %-24s %5.1f" % (t["action"], t["value"]))
    io.open("data/_energy_summary.txt", "w", encoding="utf-8").write("\n".join(L))
    print("ok")


if __name__ == "__main__":
    main()
