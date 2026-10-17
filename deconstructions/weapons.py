# -*- coding: utf-8 -*-
"""《鸣潮》武器拆解 05：白值分布。

武器的基础攻击直接进「白值」，而白值又是所有百分比攻击的乘数。
所以武器的价值不只是它自己加多少，还包括它抬高了后面每一个百分点。

用法:
    python deconstructions/weapons.py <weapon.json> --json out.json
"""
from __future__ import annotations

import io
import json
import sys
from collections import Counter, defaultdict

RARITY_NAME = {1: "1★", 2: "2★", 3: "3★", 4: "4★", 5: "5★"}


def percentile(sorted_vals, p):
    if not sorted_vals:
        return None
    idx = int(round((len(sorted_vals) - 1) * p))
    return sorted_vals[idx]


def analyse(data):
    by_rank = defaultdict(list)
    subs = defaultdict(Counter)
    for wid, w in data.items():
        r = w.get("rank")
        atk = w.get("atk")
        if r is None or not isinstance(atk, (int, float)):
            continue
        by_rank[r].append(atk)
        subs[r][w.get("sub") or "-"] += 1

    ranks = []
    for r in sorted(by_rank):
        vals = sorted(by_rank[r])
        ranks.append({
            "rank": r,
            "label": RARITY_NAME.get(r, str(r)),
            "count": len(vals),
            "min": vals[0],
            "median": percentile(vals, 0.5),
            "max": vals[-1],
        })

    # 五星与四星的中位差，以及在典型攻击加成下的实际面板差
    five = next((x for x in ranks if x["rank"] == 5), None)
    four = next((x for x in ranks if x["rank"] == 4), None)
    gap = (five["median"] - four["median"]) if five and four else None
    scenarios = []
    if gap:
        for pct in (0.0, 0.5, 1.0, 1.5, 2.0):
            scenarios.append({
                "atk_pct": pct,
                "final_gap": round(gap * (1 + pct)),
            })

    return {
        "weapon_count": len(data),
        "by_rank": ranks,
        "five_minus_four_median": gap,
        "scenarios": scenarios,
        "substats": {RARITY_NAME.get(r, str(r)): dict(c) for r, c in subs.items()},
    }


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else r"data\nanoka\3.7\weapon.json"
    data = json.load(io.open(path, encoding="utf-8"))
    res = analyse(data)

    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
        io.open(out, "w", encoding="utf-8").write(
            json.dumps(res, ensure_ascii=False, indent=1))

    L = ["武器 %d 把" % res["weapon_count"], "",
         "== 基础攻击（白值）=="]
    for r in res["by_rank"]:
        L.append("  %-3s %2d 把   %4d ~ %4d   中位 %4d"
                 % (r["label"], r["count"], r["min"], r["max"], r["median"]))
    L.append("")
    L.append("五星中位比四星高 %s 点白值" % res["five_minus_four_median"])
    L.append("== 换算成最终面板（白值差 × (1+攻击加成)）==")
    for s in res["scenarios"]:
        L.append("  攻击加成 %3.0f%%  ->  面板差 %4d"
                 % (s["atk_pct"] * 100, s["final_gap"]))
    L.append("")
    L.append("== 副属性种类 ==")
    for label, c in res["substats"].items():
        L.append("  %-3s %s" % (label, c))
    io.open("data/_weapons_summary.txt", "w", encoding="utf-8").write("\n".join(L))
    print("ok")


if __name__ == "__main__":
    main()
