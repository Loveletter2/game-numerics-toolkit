# -*- coding: utf-8 -*-
"""《鸣潮》角色拆解 07：基础面板成长。

每个角色从 1 级到 90 级，生命/攻击/防御是怎么长的，突破时跳多少。

用法:
    python deconstructions/stats.py <zh_character 目录> --json out.json
"""
from __future__ import annotations

import glob
import io
import json
import os
import sys
from collections import defaultdict

KEY_LEVELS = (1, 20, 40, 60, 80, 90)


def flatten(stats: dict) -> dict[int, dict]:
    """stats 是按突破阶段分的，同一等级可能出现在多个阶段里。

    展平成 level -> {life, atk, def}，同等级取阶段序号最大的那个
    （后期的阶段是更「正确」的值）。
    """
    out: dict[int, dict] = {}
    for phase in sorted(stats, key=lambda x: int(x)):
        for lv, row in stats[phase].items():
            try:
                level = int(lv)
            except ValueError:
                continue
            if not isinstance(row, dict):
                continue
            out[level] = {
                "life": row.get("life"),
                "atk": row.get("atk"),
                "def": row.get("def"),
            }
    return out


def load_dir(path: str):
    chars = []
    for fp in glob.glob(os.path.join(path, "*.json")):
        try:
            d = json.load(io.open(fp, encoding="utf-8"))
        except Exception:
            continue
        stats = d.get("stats")
        if not stats or not isinstance(stats, dict):
            continue
        series = flatten(stats)
        if not series:
            continue
        chars.append({
            "id": d.get("id"),
            "name": (d.get("zh") or {}).get("name") if isinstance(d.get("zh"), dict) else d.get("name"),
            "rarity": d.get("rarity"),
            "series": series,
        })
    return chars


def analyse(chars):
    rows = []
    for c in chars:
        s = c["series"]
        if 1 not in s or 90 not in s:
            continue
        a1, a90 = s[1]["atk"], s[90]["atk"]
        if not a1 or not a90:
            continue
        rows.append({
            "name": c["name"],
            "rarity": c["rarity"],
            "atk1": a1,
            "atk90": a90,
            "multiple": round(a90 / a1, 2),
            "life90": s[90].get("life"),
        })

    by_rarity = defaultdict(list)
    for r in rows:
        by_rarity[r["rarity"]].append(r)

    rarity_rows = []
    for rar in sorted(by_rarity, reverse=True):
        arr = by_rarity[rar]
        multiples = sorted(x["multiple"] for x in arr)
        atk90 = sorted(x["atk90"] for x in arr)
        rarity_rows.append({
            "rarity": rar,
            "count": len(arr),
            "median_multiple": multiples[len(multiples) // 2],
            "min_multiple": multiples[0],
            "max_multiple": multiples[-1],
            "median_atk90": round(atk90[len(atk90) // 2], 1),
            "min_atk90": round(atk90[0], 1),
            "max_atk90": round(atk90[-1], 1),
        })

    # 突破跳变：相邻等级里涨幅异常大的那几个
    jumps = []
    for c in chars:
        s = c["series"]
        levels = sorted(s)
        for i in range(1, len(levels)):
            prev, cur = levels[i - 1], levels[i]
            a0 = s[prev].get("atk")
            a1 = s[cur].get("atk")
            if not a0 or not a1:
                continue
            ratio = a1 / a0
            if ratio >= 1.14 and cur - prev <= 1:
                jumps.append({"name": c["name"], "level": cur,
                              "prev_level": prev, "ratio": round(ratio, 3),
                              "atk_prev": a0, "atk_cur": a1})

    # 每个关键等级的中位攻击（按 5 星）
    five = [c for c in chars if c["rarity"] == 5 and 90 in c["series"]]
    curve = []
    for lv in KEY_LEVELS:
        vals = sorted(c["series"][lv]["atk"] for c in five
                      if lv in c["series"] and c["series"][lv].get("atk"))
        if vals:
            curve.append({"level": lv, "median_atk": round(vals[len(vals) // 2], 1),
                          "count": len(vals)})

    return {
        "characters": len(chars),
        "analysed": len(rows),
        "by_rarity": rarity_rows,
        "curve_5star": curve,
        "jump_count": len(jumps),
        "top_jumps": sorted(jumps, key=lambda x: -x["ratio"])[:10],
    }


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else r"data\nanoka\3.7\zh_character"
    res = analyse(load_dir(path))

    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
        io.open(out, "w", encoding="utf-8").write(
            json.dumps(res, ensure_ascii=False, indent=1))

    L = ["角色文件 %d 个，1 级与 90 级数据齐全的 %d 个"
         % (res["characters"], res["analysed"]), "",
         "== 按稀有度 ==",
         "稀有度 人数  Lv90攻击中位  Lv1→90 倍数"]
    for r in res["by_rarity"]:
        L.append("%-5s %3d   %8.1f     %.2f（%.2f～%.2f）"
                 % (r["rarity"], r["count"], r["median_atk90"],
                    r["median_multiple"], r["min_multiple"], r["max_multiple"]))
    L.append("")
    L.append("== 五星的攻击成长曲线 ==")
    for c in res["curve_5star"]:
        L.append("  Lv%-3d 中位 %7.1f （%d 人）" % (c["level"], c["median_atk"], c["count"]))
    L.append("")
    L.append("== 单级涨幅 >=14%% 的跳变（共 %d 处，列前 10）==" % res["jump_count"])
    for j in res["top_jumps"]:
        L.append("  %-8s Lv%d→%d  %.1f → %.1f  (+%.1f%%)"
                 % (j["name"], j["prev_level"], j["level"],
                    j["atk_prev"], j["atk_cur"], (j["ratio"] - 1) * 100))
    io.open("data/_stats_summary.txt", "w", encoding="utf-8").write("\n".join(L))
    print("ok")


if __name__ == "__main__":
    main()
