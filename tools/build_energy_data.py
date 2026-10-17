# -*- coding: utf-8 -*-
"""从官方角色数据里抽出「每个角色有哪些给能量的动作」。

输出一份可直接内嵌进 HTML 的 JSON：
    { "characters": [ {name, cost, skills: [{name, type, concerto, source}]} ] }

来源两类：
  - 官方技能数据里明确写了「回复协奏能量」的 → source = "official"
  - 没有固定值的（普攻 / 重击 / 共鸣技能）→ 按动作表的类型中位数估，
    source = "estimate"，并在页面上标明
"""
from __future__ import annotations

import glob
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from numerics.economy import build_levels  # noqa: F401  (仅确保包可导入)

# 动作表里各类型的协奏回收中位数（第 02 篇的统计口径）
TYPE_MEDIAN = {
    "常态攻击": 1.0,
    "重击": 1.67,
    "共鸣技能": 3.5,
    "共鸣解放": 20.0,
    "变奏技能": 10.0,
    "共鸣回路": 0.0,
}

TYPE_LABEL = {
    "常态攻击": "普攻",
    "重击": "重击",
    "共鸣技能": "共鸣技能",
    "共鸣解放": "共鸣解放",
    "变奏技能": "变奏",
    "共鸣回路": "回路",
    "延奏技能": "延奏",
}


def _num(v):
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return None


def load_character(path: str) -> dict | None:
    try:
        d = json.load(io.open(path, encoding="utf-8"))
    except Exception:
        return None

    name = d.get("name") or d.get("id")
    if not name:
        return None

    cost = None
    skills: list[dict] = []
    seen = set()

    for node in (d.get("skill_trees") or {}).values():
        sk = node.get("skill") or {}
        stype = sk.get("type") or ""
        stitle = sk.get("name") or ""

        for lv in (sk.get("level") or {}).values():
            label = str(lv.get("name") or "")
            params = lv.get("param") or [[]]
            first = params[0][0] if params and params[0] else None

            if "消耗共鸣能量" in label:
                v = _num(first)
                if v:
                    cost = v
                continue

            if "回复协奏能量" not in label:
                continue

            v = _num(first)
            if v is None:
                continue

            # 去掉「…回复协奏能量」后缀，留下动作名
            act = label.split("回复协奏能量")[0].strip() or stitle
            act = act or stitle or stype
            key = (act, round(v, 3))
            if key in seen:
                continue
            seen.add(key)

            skills.append({
                "name": act,
                "type": TYPE_LABEL.get(stype, stype or "其他"),
                "concerto": round(v, 3),
                "source": "official",
            })

    # 补上按类型估算的通用动作，方便搭配固定值使用
    for stype, label in TYPE_LABEL.items():
        if stype in ("共鸣解放", "变奏技能", "延奏技能"):
            continue
        val = TYPE_MEDIAN.get(stype)
        if not val:
            continue
        skills.append({
            "name": "%s（按段计）" % label,
            "type": label,
            "concerto": val,
            "source": "estimate",
        })

    if not skills:
        return None

    return {
        "name": name,
        "cost": cost or 125.0,
        "elements": d.get("element") or "",
        "skills": skills,
    }


def main() -> int:
    src = sys.argv[1] if len(sys.argv) > 1 else r"data\nanoka\3.7\zh_character"
    out = sys.argv[2] if len(sys.argv) > 2 else r"docs\tools\energy-data.js"

    chars = []
    for fp in sorted(glob.glob(os.path.join(src, "*.json"))):
        c = load_character(fp)
        if c:
            chars.append(c)
    chars.sort(key=lambda c: c["name"])

    payload = {
        "generatedFrom": "官方角色数据（nanoka.cc 3.7）",
        "ratio": 0.5,
        "concertoCap": 100,
        "typeMedian": TYPE_MEDIAN,
        "characters": chars,
    }

    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    js = "window.ENERGY_DATA = " + json.dumps(payload, ensure_ascii=False, indent=1) + ";\n"
    io.open(out, "w", encoding="utf-8", newline="\n").write(js)

    print("角色 %d 个 -> %s" % (len(chars), out))
    official = sum(1 for c in chars for s in c["skills"] if s["source"] == "official")
    print("固定值条目 %d 条" % official)
    if chars:
        print("样例：%s 需求 %s，技能 %d 条"
              % (chars[0]["name"], chars[0]["cost"], len(chars[0]["skills"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
