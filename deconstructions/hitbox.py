# -*- coding: utf-8 -*-
"""《鸣潮》动作帧拆解 09：攻击判定范围。

一个攻击能不能打到人，取决于它挂的是什么形状、多大。

用法:
    python deconstructions/hitbox.py <动作数据表.xlsx> --json out.json
"""
from __future__ import annotations

import io
import json
import re
import sys
from collections import Counter

from _shared import load_actions, sheet_rows

SHAPE_RE = re.compile(r"^\s*(矩形|圆柱|球形|扇形|指定目标)")
NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")

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


def parse(text: str):
    if not isinstance(text, str):
        return None
    m = SHAPE_RE.match(text)
    if not m:
        return None
    shape = m.group(1)
    nums = [float(x) for x in NUM_RE.findall(text[m.end():])][:3]
    if not nums:
        return {"shape": shape, "dims": []}
    return {"shape": shape, "dims": nums}


def load_raw(xlsx):
    out = []
    for sheet in ("角色-女", "角色-男"):
        for r in sheet_rows(xlsx, sheet):
            if not r or len(r) < 48:
                continue
            action = r[2]
            if not action or not str(action).strip():
                continue
            parsed = parse(r[47])
            if not parsed:
                continue
            out.append({
                "action": str(action).strip(),
                "cat": category_of(str(action)),
                "shape": parsed["shape"],
                "dims": parsed["dims"],
            })
    return out


def analyse(rows):
    shapes = Counter(r["shape"] for r in rows)

    by_cat = {}
    for r in rows:
        d = by_cat.setdefault(r["cat"], Counter())
        d[r["shape"]] += 1

    # 矩形按第一维（长度）看大小；圆柱按半径
    rect_len = sorted(r["dims"][0] for r in rows
                      if r["shape"] == "矩形" and r["dims"])
    cyl_r = sorted(r["dims"][0] for r in rows
                   if r["shape"] == "圆柱" and r["dims"])

    def med(arr):
        return arr[len(arr) // 2] if arr else None

    # 体积近似，用来找最大的 AoE
    big = []
    for r in rows:
        d = r["dims"]
        if not d:
            continue
        if r["shape"] == "矩形" and len(d) >= 3:
            vol = d[0] * d[1] * d[2]
        elif r["shape"] == "圆柱" and len(d) >= 3:
            vol = 3.1416 * d[0] * d[0] * d[2]
        elif r["shape"] == "球形" and len(d) >= 1:
            vol = 4.1888 * d[0] ** 3
        else:
            continue
        big.append({"action": r["action"], "shape": r["shape"],
                    "dims": d, "volume": round(vol)})
    big.sort(key=lambda x: -x["volume"])

    return {
        "rows": len(rows),
        "shapes": dict(shapes.most_common()),
        "by_category": {k: dict(v.most_common()) for k, v in by_cat.items()},
        "rect_length_median": med(rect_len),
        "rect_length_min": rect_len[0] if rect_len else None,
        "rect_length_max": rect_len[-1] if rect_len else None,
        "cyl_radius_median": med(cyl_r),
        "cyl_radius_max": cyl_r[-1] if cyl_r else None,
        "largest": big[:8],
    }


def main():
    xlsx = sys.argv[1] if len(sys.argv) > 1 else r"data\鸣潮动作数据汇总.xlsx"
    res = analyse(load_raw(xlsx))

    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
        io.open(out, "w", encoding="utf-8").write(
            json.dumps(res, ensure_ascii=False, indent=1))

    L = ["带判定范围的攻击 %d 条" % res["rows"], "",
         "== 形状分布 =="]
    for k, n in res["shapes"].items():
        L.append("  %-6s %4d 条  %5.1f%%" % (k, n, n / res["rows"] * 100))
    L.append("")
    L.append("== 按动作类型 ==")
    for cat, d in sorted(res["by_category"].items(), key=lambda kv: -sum(kv[1].values())):
        total = sum(d.values())
        top = "，".join("%s %d" % (k, v) for k, v in sorted(d.items(), key=lambda kv: -kv[1])[:3])
        L.append("  %-10s %4d 条：%s" % (cat, total, top))
    L.append("")
    L.append("矩形长度 中位 %s，范围 %s～%s"
             % (res["rect_length_median"], res["rect_length_min"], res["rect_length_max"]))
    L.append("圆柱半径 中位 %s，最大 %s"
             % (res["cyl_radius_median"], res["cyl_radius_max"]))
    L.append("")
    L.append("== 体积最大的 8 个 ==")
    for b in res["largest"]:
        L.append("  %-24s %s %s  体积≈%s"
                 % (b["action"], b["shape"],
                    "(" + ",".join("%g" % x for x in b["dims"]) + ")",
                    format(b["volume"], ",")))
    io.open("data/_hitbox_summary.txt", "w", encoding="utf-8").write("\n".join(L))
    print("ok")


if __name__ == "__main__":
    main()
