# -*- coding: utf-8 -*-
"""《鸣潮》拆解 08：声骸套装的效果结构。

2 件套给什么，5 件套给什么，两者是不是同一类东西。

用法:
    python deconstructions/sonata.py <sonata.json> --json out.json
"""
from __future__ import annotations

import io
import json
import sys
from collections import Counter, defaultdict

# 按中文描述里的关键词归类
KINDS = [
    ("伤害加成", ("伤害加成", "伤害提升", "伤害增加")),
    ("暴击", ("暴击",)),
    ("攻击", ("攻击",)),
    ("生命", ("生命",)),
    ("防御", ("防御",)),
    ("充能", ("共鸣效率", "充能")),
    ("治疗", ("治疗",)),
    ("机制/其他", ()),
]


def classify(desc: str) -> str:
    for label, keys in KINDS:
        if any(k in desc for k in keys):
            return label
    return "机制/其他"


def analyse(data):
    rows = []
    for sid, s in data.items():
        name = (s.get("name") or {}).get("zh") or sid
        pieces = s.get("set") or {}
        for count in ("2", "5"):
            block = pieces.get(count)
            if not block:
                continue
            zh = block.get("zh") or {}
            desc = (zh.get("desc") or "").strip()
            params = zh.get("param") or []
            if not desc:
                continue
            rows.append({
                "set": name,
                "piece": count,
                "desc": desc,
                "params": params,
                "kind": classify(desc),
            })

    by_piece = {}
    for count in ("2", "5"):
        subset = [r for r in rows if r["piece"] == count]
        by_piece[count] = {
            "count": len(subset),
            "kinds": dict(Counter(r["kind"] for r in subset).most_common()),
            "with_param": sum(1 for r in subset if r["params"]),
            "long_desc": sum(1 for r in subset if len(r["desc"]) > 40),
        }

    return {"sets": len(data), "by_piece": by_piece, "rows": rows}


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else r"data\nanoka\3.7\sonata.json"
    data = json.load(io.open(path, encoding="utf-8"))
    res = analyse(data)

    if "--json" in sys.argv:
        out = sys.argv[sys.argv.index("--json") + 1]
        io.open(out, "w", encoding="utf-8").write(
            json.dumps(res, ensure_ascii=False, indent=1))

    L = ["套装 %d 套" % res["sets"], ""]
    for count, info in res["by_piece"].items():
        L.append("%s 件套：%d 条" % (count, info["count"]))
        L.append("   类型分布：%s" % info["kinds"])
        L.append("   带数值参数的：%d 条" % info["with_param"])
        L.append("   描述超过 40 字的：%d 条" % info["long_desc"])
        L.append("")
    L.append("== 5 件套里描述最长的 6 条 ==")
    five = sorted([r for r in res["rows"] if r["piece"] == "5"],
                  key=lambda r: -len(r["desc"]))[:6]
    for r in five:
        L.append("  %s：%s" % (r["set"], r["desc"][:60]))
    io.open("data/_sonata_summary.txt", "w", encoding="utf-8").write("\n".join(L))
    print("ok")


if __name__ == "__main__":
    main()
