# -*- coding: utf-8 -*-
"""重新生成 deconstructions 系列的全部图表。

每张图都从原始数据重算，不读缓存。工作簿只加载一次，避免重复 I/O。

用法:
    python deconstructions/charts.py [数据表.xlsx] [nanoka 目录]
"""
from __future__ import annotations

import glob
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from numerics.charts import h_bar_chart, line_chart      # noqa: E402

import changelog     # noqa: E402
import energy        # noqa: E402
import energy_budget  # noqa: E402
import enemies       # noqa: E402
import hitbox        # noqa: E402
import multipliers   # noqa: E402
import poise         # noqa: E402
import recovery      # noqa: E402
import sonata        # noqa: E402
import stats as stats_mod   # noqa: E402
import weapons       # noqa: E402
from _shared import load_actions      # noqa: E402

OUT = os.path.join("docs", "img")


def main():
    xlsx = sys.argv[1] if len(sys.argv) > 1 else r"data\鸣潮动作数据汇总.xlsx"
    nanoka = sys.argv[2] if len(sys.argv) > 2 else r"data\nanoka\3.7"
    made = []

    # ---------- 一次加载，多处复用 ----------
    rows = load_actions(xlsx)

    # 02 协奏：按档位
    e = energy.analyse(rows)
    labels = [k for k, v in e["buckets"].items() if v]
    vals = [e["buckets"][k] for k in labels]
    made.append(h_bar_chart(
        labels, vals, os.path.join(OUT, "concerto-buckets.svg"),
        title="协奏能量：单次给多少（按档位统计动作数）",
        xlabel="动作数", value_suffix=" 条"))

    # 03 削韧：按类型中位数
    p = poise.analyse(rows)
    cats = [c["category"] for c in p["by_category"]]
    meds = [c["median"] for c in p["by_category"]]
    made.append(h_bar_chart(
        cats, meds, os.path.join(OUT, "poise-by-category.svg"),
        title="削韧值：各类型的中位数",
        xlabel="削韧值中位数", value_suffix=""))

    # 04 后摇：按类型中位数
    r = recovery.analyse(rows)
    cats = [c["category"] for c in r["by_category"]]
    recs = [c["median_recovery"] for c in r["by_category"]]
    made.append(h_bar_chart(
        cats, recs, os.path.join(OUT, "recovery-by-category.svg"),
        title="后摇长度：各类型的中位数（帧，60fps）",
        xlabel="帧", value_suffix="F"))

    # 09 判定形状
    h = hitbox.analyse(hitbox.load_raw(xlsx))
    made.append(h_bar_chart(
        list(h["shapes"].keys()), list(h["shapes"].values()),
        os.path.join(OUT, "hitbox-shapes.svg"),
        title="攻击判定：形状分布",
        xlabel="动作数", value_suffix=" 条"))

    # ---------- nanoka 数据 ----------
    weapon_data = json.load(io.open(os.path.join(nanoka, "weapon.json"),
                                    encoding="utf-8"))
    w = weapons.analyse(weapon_data)
    made.append(h_bar_chart(
        [x["label"] for x in w["by_rank"]],
        [x["median"] for x in w["by_rank"]],
        os.path.join(OUT, "weapon-atk-by-rarity.svg"),
        title="武器基础攻击：各稀有度的中位数",
        xlabel="基础攻击", value_suffix=""))

    sonata_data = json.load(io.open(os.path.join(nanoka, "sonata.json"),
                                    encoding="utf-8"))
    so = sonata.analyse(sonata_data)
    two = so["by_piece"]["2"]
    five = so["by_piece"]["5"]
    made.append(h_bar_chart(
        ["2 件套", "5 件套"],
        [two["long_desc"] / two["count"] * 100,
         five["long_desc"] / five["count"] * 100],
        os.path.join(OUT, "sonata-longdesc.svg"),
        title="需要一段话来描述的套装效果占比",
        xlabel="占比", value_suffix="%"))

    chars = stats_mod.load_dir(os.path.join(nanoka, "zh_character"))
    st = stats_mod.analyse(chars)
    levels = [c["level"] for c in st["curve_5star"]]
    atks = [c["median_atk"] for c in st["curve_5star"]]
    made.append(line_chart(
        {"五星攻击中位": (levels, atks)},
        os.path.join(OUT, "atk-growth.svg"),
        title="五星角色的攻击力成长（中位数）",
        xlabel="等级", ylabel="攻击力"))

    m = multipliers.analyse(multipliers.load_dir(os.path.join(nanoka, "zh_character")))
    share = m["share_by_type"]
    made.append(h_bar_chart(
        list(share.keys()), list(share.values()),
        os.path.join(OUT, "multiplier-share.svg"),
        title="技能倍率都花在哪：按技能类型占比",
        xlabel="占比", value_suffix="%"))

    en = enemies.analyse(enemies.load(xlsx), 90695.0)
    tiers = en.get("tiers") or []
    if tiers:
        made.append(h_bar_chart(
            ["Lv%d" % x["level"] for x in tiers],
            [x["ttk"] for x in tiers],
            os.path.join(OUT, "enemy-ttk.svg"),
            title="打掉该等级最常见血量需要多久（DPS 90,695）",
            xlabel="秒", value_suffix=" 秒"))

    cl = changelog.analyse(
        changelog.load_changes(xlsx),
        changelog.load_names(os.path.join(nanoka, "zh_character")))
    kinds = cl["kinds"]
    made.append(h_bar_chart(
        list(kinds.keys()), list(kinds.values()),
        os.path.join(OUT, "changelog-kinds.svg"),
        title="更新日志：改动类型分布",
        xlabel="条目数", value_suffix=" 条"))

    eb = energy_budget.analyse(energy_budget.load(os.path.join(nanoka, "zh_character")))
    made.append(h_bar_chart(
        ["%g 点大招" % r["cost"] for r in eb["by_cost"]],
        [r["coverage"] for r in eb["by_cost"]],
        os.path.join(OUT, "energy-budget.svg"),
        title="技能组固定充能占大招需求的比例",
        xlabel="占比", value_suffix="%"))

    for p_ in made:
        print("wrote", p_)
    print("total", len(made))


if __name__ == "__main__":
    main()
