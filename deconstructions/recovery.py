# -*- coding: utf-8 -*-
"""《鸣潮》动作帧拆解 04：动作时长与后摇。

一个动作从起手到能再次行动，中间有多少时间是「打完了但还不能动」。

用法:
    python deconstructions/recovery.py <动作数据表.xlsx> --json out.json
"""
from __future__ import annotations

import io
import json
import sys
from collections import Counter

from _shared import FPS, load_actions

CATEGORY = [
    ("共鸣解放", ("大招", "解放")),
    ("变奏/延奏", ("变奏", "延奏", "同奏")),
    ("共鸣技能", ("E", "共鸣技能")),
    ("重击", ("重击",)),
    ("普攻", ("普攻",)),
    ("闪避/反击", ("闪避", "反击")),
]


def category_of(action: str) -> str:
    for label, keys in CATEGORY:
        if any(k in action for k in keys):
            return label
    return "其他"


def analyse(rows):
    usable = []
    for r in rows:
        s, d, e = r["startup"], r["duration"], r["end"]
        if not e or not s:
            continue
        if e < s:
            continue
        active = (d or 0)
        recovery = e - s - active
        if recovery < 0:
            recovery = 0
        usable.append({
            "action": r["action"],
            "cat": category_of(r["action"]),
            "frames": e,
            "seconds": round(e / FPS, 3),
            "recovery": recovery,
            "recovery_pct": round(recovery / e * 100, 1),
            "hitstop": r["hitstop_self"] or 0,
        })

    total_frames = sorted(x["frames"] for x in usable)

    by_cat = {}
    for x in usable:
        by_cat.setdefault(x["cat"], []).append(x)

    cat_rows = []
    for cat, arr in by_cat.items():
        if len(arr) < 10:
            continue
        lens = sorted(a["frames"] for a in arr)
        recs = sorted(a["recovery"] for a in arr)
        pcts = sorted(a["recovery_pct"] for a in arr)
        cat_rows.append({
            "category": cat,
            "count": len(arr),
            "median_length": lens[len(lens) // 2],
            "median_recovery": recs[len(recs) // 2],
            "median_pct": round(pcts[len(pcts) // 2], 1),
        })
    cat_rows.sort(key=lambda x: -x["median_pct"])

    # 后摇最长的动作
    longest = sorted(usable, key=lambda x: -x["recovery"])[:8]

    hitstops = [r["hitstop_self"] for r in rows if r["hitstop_self"]]
    return {
        "row_count": len(rows),
        "usable": len(usable),
        "median_frames": total_frames[len(total_frames) // 2],
        "median_seconds": round(total_frames[len(total_frames) // 2] / FPS, 3),
        "by_category": cat_rows,
        "longest_recovery": [{"action": x["action"], "cat": x["cat"],
                              "recovery": x["recovery"],
                              "pct": x["recovery_pct"]} for x in longest],
        "hitstop_median": sorted(hitstops)[len(hitstops) // 2] if hitstops else None,
        "hitstop_max": max(hitstops) if hitstops else None,
    }


def main():
    xlsx = sys.argv[1] if len(sys.argv) > 1 else r"data\鸣潮动作数据汇总.xlsx"
    res = analyse(load_actions(xlsx))

    if "--json" in sys.argv:
        path = sys.argv[sys.argv.index("--json") + 1]
        io.open(path, "w", encoding="utf-8").write(
            json.dumps(res, ensure_ascii=False, indent=1))

    L = [
        "动作 %d 个，起手帧和结束帧都齐全的 %d 个" % (res["row_count"], res["usable"]),
        "完整动作长度中位 %dF（%.2fs）" % (res["median_frames"], res["median_seconds"]),
        "顿帧中位 %sF，最大 %sF" % (res["hitstop_median"], res["hitstop_max"]),
        "",
        "== 按类型：动作长度 / 后摇 / 后摇占比 ==",
    ]
    for c in res["by_category"]:
        L.append("  %-10s %4d 条  长度%5.0fF  后摇%5.0fF  占比%5.1f%%"
                 % (c["category"], c["count"], c["median_length"],
                    c["median_recovery"], c["median_pct"]))
    L.append("")
    L.append("== 后摇最长的动作 ==")
    for x in res["longest_recovery"]:
        L.append("  %-24s 后摇 %5.0fF  占全长 %5.1f%%  [%s]"
                 % (x["action"], x["recovery"], x["pct"], x["cat"]))
    io.open("data/_recovery_summary.txt", "w", encoding="utf-8").write("\n".join(L))
    print("ok")


if __name__ == "__main__":
    main()
